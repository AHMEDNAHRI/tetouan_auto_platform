import json
import random
import joblib
import numpy as np
import psycopg2
import sys
import os
from kafka import KafkaConsumer
from score_engine import compute_svc
from lstm_model import compute_lstm_score

# ─── Import Notifications ───────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), '../api'))
try:
    from notifications import send_notification
    NOTIF_OK = True
    print("✅ Module notifications charge !")
except Exception as e:
    NOTIF_OK = False
    print(f"⚠️  Notifications non disponibles : {e}")

# ─── Charger K-Means si disponible ──────────────────────────────────
try:
    km_model = joblib.load(
        "../ml_models/kmeans_model.pkl"
    )
    km_scaler = joblib.load(
        "../ml_models/kmeans_scaler.pkl"
    )
    KMEANS_OK = True
    print("✅ K-Means charge !")
except:
    KMEANS_OK = False
    print("⚠️  K-Means pas encore disponible")

# ─── Connexion PostgreSQL ────────────────────────────────────────────
conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="tetouan_auto",
    user="admin",
    password="admin123"
)
cursor = conn.cursor()
print("✅ Connexion PostgreSQL OK !")

# ─── Connexion Kafka ─────────────────────────────────────────────────
consumer = KafkaConsumer(
    'tetouan_auto_events',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(
        x.decode('utf-8')
    )
)
print("✅ Consumer demarre !")
print("─" * 60)

# ─── Compteur pour éviter spam notifications ─────────────────────────
notif_counter = {}   # {client_id: nb_notifications}
NOTIF_MAX_PAR_CLIENT = 3  # Max 3 notifs par client par session

def get_client_segment(client_id):
    """Recupere le segment K-Means du client"""
    if not KMEANS_OK:
        return "INCONNU"
    try:
        cursor.execute("""
            SELECT 
                AVG(c1_frequence) as freq,
                AVG(c3_valeur)    as valeur,
                AVG(c5_delai)     as delai,
                COUNT(*)          as nb
            FROM gold_scores
            WHERE client_id = %s
        """, (client_id,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            features = np.array([[
                row[0] or 0,
                row[1] or 0,
                row[2] or 0,
                row[3] or 0
            ]])
            features_scaled = km_scaler.transform(features)
            cluster = km_model.predict(features_scaled)[0]
            segments = {
                0: 'VIP',
                1: 'REGULIER',
                2: 'OCCASIONNEL',
                3: 'INACTIF'
            }
            return segments.get(cluster, 'INCONNU')
    except:
        pass
    return "INCONNU"


def should_send_notification(client_id, alert_level):
    """
    Decide si on envoie une notification.
    Regles :
      - Seulement CRITIQUE ou MODEREE
      - Max NOTIF_MAX_PAR_CLIENT par client par session
    """
    if alert_level not in ('CRITIQUE', 'MODEREE'):
        return False

    count = notif_counter.get(client_id, 0)
    if count >= NOTIF_MAX_PAR_CLIENT:
        return False

    return True


# ════════════════════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ════════════════════════════════════════════════════════════════════
for message in consumer:
    event = message.value

    # ── 1 — Sauvegarder dans Bronze ──────────────────────────────────
    cursor.execute("""
        INSERT INTO bronze_events
        (client_id, event_type, car_id, amount,
         status, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        event['client_id'],
        event['event_type'],
        event['car_id'],
        event['amount'],
        event['status'],
        json.dumps(event)
    ))

    # ── 2 — Score LSTM reel ───────────────────────────────────────────
    lstm_score = compute_lstm_score(event['client_id'])

    # ── 3 — Calculer SVC avec LSTM reel ──────────────────────────────
    features = {
        'frequence':     random.randint(1, 20),
        'anciennete':    random.randint(1, 60),
        'valeur':        event['amount'],
        'sav_mobilite':  random.uniform(0, 1),
        'delai_contact': random.randint(1, 365),
        'lstm_drift':    lstm_score,
    }
    result = compute_svc(features)

    # ── 4 — Segment K-Means ───────────────────────────────────────────
    segment = get_client_segment(event['client_id'])

    # ── 5 — Sauvegarder dans Gold ─────────────────────────────────────
    cursor.execute("""
        INSERT INTO gold_scores
        (client_id, svc_score, alert_level,
         decision, c1_frequence, c2_anciennete,
         c3_valeur, c4_sav_mobilite, c5_delai,
         c6_lstm, processing_time_ms,
         client_segment, lstm_score_reel)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        event['client_id'],
        result['svc_score'],
        result['alert_level'],
        result['decision'],
        result['c1_frequence'],
        result['c2_anciennete'],
        result['c3_valeur'],
        result['c4_sav_mobilite'],
        result['c5_delai'],
        result['c6_lstm'],
        result['processing_ms'],
        segment,
        lstm_score
    ))

    conn.commit()

    # ── 6 — Affichage console ─────────────────────────────────────────
    emoji = {"CRITIQUE": "🔴", "MODEREE": "🟠", "NORMAL": "🟢"}
    niveau = result['alert_level']

    print(
        f"{emoji.get(niveau, '⚪')} "
        f"[{niveau}] "
        f"Client {event['client_id']} "
        f"({segment}) "
        f"Score {result['svc_score']:.2f} "
        f"LSTM {lstm_score:.2f} "
        f"→ {result['decision']} "
        f"({result['processing_ms']:.1f}ms)"
    )

    # ── 7 — Envoyer Notification si Alerte ───────────────────────────
    if NOTIF_OK and should_send_notification(
        event['client_id'],
        result['alert_level']
    ):
        try:
            send_notification(
                client_id=event['client_id'],
                score=result['svc_score'],
                alert_level=result['alert_level'],
                decision=result['decision'],
                segment=segment
            )

            # Incrémenter compteur anti-spam
            notif_counter[event['client_id']] = (
                notif_counter.get(event['client_id'], 0) + 1
            )

            print(
                f"   📧 Notification envoyee "
                f"(client {event['client_id']}, "
                f"{result['alert_level']})"
            )

        except Exception as e:
            print(f"   ⚠️  Erreur notification : {e}")