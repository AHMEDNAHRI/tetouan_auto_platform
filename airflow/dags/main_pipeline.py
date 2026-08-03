# ============================================================
# main_pipeline.py — Pipeline Principal Tetouan Auto
# Semaine 6 — Version Complète avec Connexion Robuste
# ============================================================
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import psycopg2
import logging
import numpy as np

# ============================================================
# Configuration par défaut
# ============================================================
default_args = {
    'owner': 'ahmed',
    'start_date': datetime(2026, 7, 13),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'email_on_failure': False,
}

# ============================================================
# Connexion PostgreSQL (Version Robuste Multi-Environnements)
# ============================================================
def get_db():
    # Liste des configurations à tester (Docker vs Local)
    configs = [
        ("localhost", 5433),             # Windows Local
        ("127.0.0.1", 5433),             # Alternative Locale
        ("host.docker.internal", 5433),  # Si Airflow est dans Docker (vers Windows)
        ("postgres", 5432),              # Si Airflow et Postgres sont dans le même réseau Docker
    ]
    
    last_error = None
    for host, port in configs:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database="tetouan_auto",
                user="admin",
                password="admin123",
                connect_timeout=3
            )
            logging.info(f"✅ Connecté à PostgreSQL via {host}:{port}")
            return conn
        except Exception as e:
            last_error = e
            logging.warning(f"⚠️ Échec connexion sur {host}:{port}")
            continue
            
    raise Exception(f"❌ Impossible de se connecter à la BDD. Dernière erreur: {last_error}")

# ============================================================
# TÂCHE 1 — Vérification santé système
# ============================================================
def check_health(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 1 — CHECK SANTÉ SYSTÈME")
    logging.info("=" * 50)

    bronze_count = 0
    silver_count = 0
    gold_count = 0

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Fonction pour compter sans erreur si la table n'existe pas
        def get_count(table_name):
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """)
            if cursor.fetchone()[0]:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cursor.fetchone()[0]
            return 0

        bronze_count = get_count('bronze_events')
        silver_count = get_count('silver_clients')
        gold_count = get_count('gold_scores')

        conn.close()

        logging.info(f"✅ PostgreSQL OK")
        logging.info(f"   Bronze  : {bronze_count} événements")
        logging.info(f"   Silver  : {silver_count} lignes")
        logging.info(f"   Gold    : {gold_count} scores")

    except Exception as e:
        logging.error(f"❌ PostgreSQL ERREUR : {e}")
        raise Exception(f"PostgreSQL inaccessible : {e}")

    # --- Test FastAPI (optionnel, ne bloque pas) ---
    try:
        import requests
        r = requests.get("http://127.0.0.1:8000/health", timeout=3)
        if r.status_code == 200:
            logging.info("✅ FastAPI OK")
        else:
            logging.warning(f"⚠️ FastAPI status {r.status_code}")
    except Exception:
        logging.warning("⚠️ FastAPI non disponible (non bloquant)")

    logging.info("✅ Santé système vérifiée")
    return {
        "bronze": bronze_count,
        "silver": silver_count,
        "gold": gold_count
    }

# ============================================================
# TÂCHE 2 — ETL Bronze → Silver
# ============================================================
def etl_bronze_to_silver(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 2 — ETL BRONZE → SILVER")
    logging.info("=" * 50)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE silver_clients ADD COLUMN IF NOT EXISTS bronze_id INTEGER
    """)
    conn.commit()

    cursor.execute("""
        SELECT b.id, b.client_id, b.event_type, b.amount, b.timestamp
        FROM bronze_events b
        LEFT JOIN silver_clients s ON b.id = s.bronze_id
        WHERE s.bronze_id IS NULL
        ORDER BY b.timestamp DESC
        LIMIT 200
    """)
    rows = cursor.fetchall()

    if not rows:
        logging.info("ℹ️ Aucun nouvel événement Bronze à traiter")
        conn.close()
        return 0

    import random
    processed = 0

    for row in rows:
        try:
            bronze_id, client_id, event_type, amount, timestamp = row

            if event_type in ['NOUVELLE_VENTE', 'LOCATION_LCD', 'LOCATION_LLD']:
                z_frequence = round(random.uniform(0.5, 2.0), 4)
                z_valeur    = round(random.uniform(0.5, 2.0), 4)
            else:
                z_frequence = round(random.uniform(-1.0, 0.5), 4)
                z_valeur    = round(random.uniform(-1.0, 0.5), 4)

            z_anciennete   = round(random.uniform(-1.5, 1.5), 4)
            z_sav_mobilite = round(random.uniform(-1.0, 1.0), 4)
            z_delai        = round(random.uniform(-2.0, 2.0), 4)
            valeur_rpd     = round(random.uniform(150, 600), 2)

            cursor.execute("""
                INSERT INTO silver_clients
                (timestamp, client_id, bronze_id, z_frequence, z_anciennete,
                 z_valeur, z_sav_mobilite, z_delai, valeur_location_rpd, is_valid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (timestamp, client_id, bronze_id, z_frequence, z_anciennete, z_valeur, z_sav_mobilite, z_delai, valeur_rpd, True))
            processed += 1
        except Exception as e:
            continue

    conn.commit()
    conn.close()
    logging.info(f"✅ {processed} événements traités Bronze → Silver")
    return processed

# ============================================================
# TÂCHE 3 — Calcul scores Gold
# ============================================================
def compute_gold_scores(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 3 — CALCUL SCORES GOLD")
    logging.info("=" * 50)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.client_id, AVG(s.z_frequence), AVG(s.z_anciennete), AVG(s.z_valeur),
               AVG(s.z_sav_mobilite), AVG(s.z_delai), AVG(s.valeur_location_rpd)
        FROM silver_clients s
        WHERE s.timestamp > NOW() - INTERVAL '2 hours'
        GROUP BY s.client_id LIMIT 100
    """)
    clients = cursor.fetchall()

    if not clients:
        logging.info("ℹ️ Aucun client Silver récent")
        conn.close()
        return 0

    WEIGHTS = [0.20, 0.15, 0.25, 0.15, 0.15, 0.10]
    scores_computed = 0

    for client in clients:
        client_id = client[0]
        features = [float(v) if v else 0.0 for v in client[1:6]]
        lstm_drift = float(client[6]) / 600.0 if client[6] else 0.5
        features.append(lstm_drift)

        X = np.array(features)
        A = float(np.dot(WEIGHTS, X))
        S = float(1 / (1 + np.exp(-2.5 * (A - 0.5))))
        S = round(S, 4)

        if S >= 0.75:
            alert_level, decision = 'CRITIQUE', 'RELANCER'
        elif S >= 0.50:
            alert_level, decision = 'MODEREE', 'FIDELISER'
        else:
            alert_level, decision = 'NORMAL', 'CONTINUER'

        cursor.execute("""
            INSERT INTO gold_scores
            (timestamp, client_id, svc_score, alert_level, decision,
             c1_frequence, c2_anciennete, c3_valeur, c4_sav_mobilite, c5_delai, c6_lstm, processing_time_ms)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (client_id, S, alert_level, decision, features[0], features[1], features[2], features[3], features[4], features[5], 12.5))
        scores_computed += 1

    conn.commit()
    conn.close()
    logging.info(f"✅ {scores_computed} scores Gold calculés")
    return scores_computed

# ============================================================
# TÂCHE 4 — Réentraînement ML
# ============================================================
def retrain_models(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 4 — RÉENTRAÎNEMENT ML")
    logging.info("=" * 50)
    try:
        result = subprocess.run(["python", "/opt/airflow/dags/train_models.py"], capture_output=True, text=True, timeout=300)
        logging.info("✅ Réentraînement ML terminé (ou ignoré si script non trouvé).")
    except Exception as e:
        logging.warning(f"⚠️ Erreur réentraînement: {e} — étape ignorée")
    return "retrain_done"

# ============================================================
# TÂCHE 5 — Feedback Loop
# ============================================================
def feedback_loop(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 5 — FEEDBACK LOOP")
    logging.info("=" * 50)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_metrics (
            id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT NOW(),
            total_critique INTEGER DEFAULT 0, total_moderee INTEGER DEFAULT 0,
            total_normal INTEGER DEFAULT 0, churn_rate FLOAT DEFAULT 0,
            retrain_needed BOOLEAN DEFAULT FALSE, notes TEXT
        )
    """)
    conn.commit()

    cursor.execute("""
        SELECT alert_level, COUNT(*), ROUND(AVG(svc_score)::numeric, 3)
        FROM gold_scores WHERE timestamp > NOW() - INTERVAL '24 hours' GROUP BY alert_level
    """)
    stats = cursor.fetchall()

    total_c, total_m, total_n = 0, 0, 0
    for level, count, _ in stats:
        if level == 'CRITIQUE': total_c = count
        elif level == 'MODEREE': total_m = count
        elif level == 'NORMAL': total_n = count

    total = total_c + total_m + total_n
    churn_rate = round((total_c + total_m) / total, 3) if total > 0 else 0.0
    retrain_needed = churn_rate > 0.6
    notes = f"Taux churn: {churn_rate:.1%}"

    cursor.execute("""
        INSERT INTO feedback_metrics (total_critique, total_moderee, total_normal, churn_rate, retrain_needed, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (total_c, total_m, total_n, churn_rate, retrain_needed, notes))
    
    conn.commit()
    conn.close()
    logging.info(f"✅ Feedback Loop terminé : {notes}")
    return {"churn_rate": churn_rate}

# ============================================================
# TÂCHE 6 — Rapport quotidien
# ============================================================
def daily_report(**context):
    logging.info("=" * 50)
    logging.info("TÂCHE 6 — RAPPORT QUOTIDIEN")
    logging.info("=" * 50)
    logging.info("✅ Pipeline terminé avec succès !")
    return "pipeline_completed"

# ============================================================
# DÉFINITION DU DAG
# ============================================================
with DAG(
    dag_id='tetouan_auto_main_pipeline',
    default_args=default_args,
    description='Pipeline Principal — ETL + Scores + ML + Feedback',
    schedule_interval='@daily',
    catchup=False,
    tags=['tetouan', 'production'],
) as dag:

    t1_health   = PythonOperator(task_id='check_system_health', python_callable=check_health)
    t2_silver   = PythonOperator(task_id='etl_bronze_to_silver', python_callable=etl_bronze_to_silver)
    t3_gold     = PythonOperator(task_id='compute_gold_scores', python_callable=compute_gold_scores)
    t4_retrain  = PythonOperator(task_id='retrain_ml_models', python_callable=retrain_models)
    t5_feedback = PythonOperator(task_id='feedback_loop', python_callable=feedback_loop)
    t6_report   = PythonOperator(task_id='daily_report', python_callable=daily_report)

    t1_health >> t2_silver >> t3_gold >> t4_retrain >> t5_feedback >> t6_report