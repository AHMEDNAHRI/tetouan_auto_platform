# api/main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
from datetime import datetime

# ============================================================
# CONFIGURATION API
# ============================================================

app = FastAPI(
    title="Tetouan Auto Intelligence API",
    description="API temps reel — Ventes, SAV & RentopCar",
    version="1.0.0"
)

# Autoriser toutes les connexions (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CONNEXION BASE DE DONNÉES
# ============================================================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="tetouan_auto",
        user="admin",
        password="admin123"
    )

# ============================================================
# ENDPOINT 1 — HEALTH CHECK
# GET /health
# ============================================================

@app.get("/health")
def health():
    """
    Vérifier que l'API tourne correctement
    """
    return {
        "status": "ok",
        "message": "Tetouan Auto API fonctionne !",
        "timestamp": str(datetime.now())
    }

# ============================================================
# ENDPOINT 2 — DERNIERS SCORES
# GET /scores/latest
# ============================================================

@app.get("/scores/latest")
def get_latest_scores():
    """
    Retourne les 20 derniers scores clients
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            id,
            client_id,
            svc_score,
            alert_level,
            decision,
            client_segment,
            lstm_score_reel,
            processing_time_ms,
            timestamp
        FROM gold_scores
        ORDER BY timestamp DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    conn.close()

    return {
        "count": len(rows),
        "scores": [dict(row) for row in rows]
    }

# ============================================================
# ENDPOINT 3 — HISTORIQUE D'UN CLIENT
# GET /scores/client/{client_id}
# ============================================================

@app.get("/scores/client/{client_id}")
def get_client_score(client_id: int):
    """
    Retourne l'historique complet d'un client
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            id,
            client_id,
            svc_score,
            alert_level,
            decision,
            client_segment,
            lstm_score_reel,
            timestamp
        FROM gold_scores
        WHERE client_id = %s
        ORDER BY timestamp DESC
        LIMIT 50
    """, (client_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "client_id": client_id,
            "message": "Client non trouve",
            "historique": []
        }

    return {
        "client_id": client_id,
        "nb_events": len(rows),
        "historique": [dict(row) for row in rows]
    }

# ============================================================
# ENDPOINT 4 — ALERTES ACTIVES
# GET /alerts/active
# ============================================================

@app.get("/alerts/active")
def get_active_alerts():
    """
    Retourne les alertes CRITIQUE et MODEREE actives
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            client_id,
            svc_score,
            alert_level,
            decision,
            client_segment,
            lstm_score_reel,
            timestamp
        FROM gold_scores
        WHERE alert_level IN ('CRITIQUE', 'MODEREE')
        ORDER BY svc_score DESC, timestamp DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()
    conn.close()

    critiques = [r for r in rows if r['alert_level'] == 'CRITIQUE']
    moderees  = [r for r in rows if r['alert_level'] == 'MODEREE']

    return {
        "total_alertes": len(rows),
        "critiques": len(critiques),
        "moderees": len(moderees),
        "alertes": [dict(row) for row in rows]
    }

# ============================================================
# ENDPOINT 5 — STATS PAR SEGMENT
# GET /segments/stats
# ============================================================

@app.get("/segments/stats")
def get_segments_stats():
    """
    Stats par segment K-Means (VIP, REGULIER, etc.)
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            client_segment,
            COUNT(DISTINCT client_id) as nb_clients,
            ROUND(AVG(svc_score)::numeric, 3)    as score_moyen,
            ROUND(AVG(lstm_score_reel)::numeric, 3) as lstm_moyen
        FROM gold_scores
        WHERE client_segment IS NOT NULL
        GROUP BY client_segment
        ORDER BY nb_clients DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return {
        "segments": [dict(row) for row in rows]
    }

# ============================================================
# ENDPOINT 6 — STATS RENTOPCAR
# GET /rentopcar/stats
# ============================================================

@app.get("/rentopcar/stats")
def get_rentopcar_stats():
    """
    KPIs RentopCar : locations LCD/LLD
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            event_type,
            COUNT(*)            as nb_events,
            ROUND(AVG(amount)::numeric, 2) as montant_moyen,
            ROUND(SUM(amount)::numeric, 2) as montant_total
        FROM bronze_events
        WHERE event_type IN (
            'LOCATION_LCD', 'LOCATION_LLD', 
            'FIN_LOCATION', 'PAIEMENT'
        )
        GROUP BY event_type
        ORDER BY nb_events DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return {
        "rentopcar_kpis": [dict(row) for row in rows]
    }

# ============================================================
# ENDPOINT 7 — DASHBOARD GLOBAL
# GET /stats/dashboard
# ============================================================

@app.get("/stats/dashboard")
def get_dashboard_stats():
    """
    KPIs globaux pour Power BI et Grafana
    """
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Stats générales
    cursor.execute("""
        SELECT 
            COUNT(*)                              as total_events,
            COUNT(DISTINCT client_id)             as total_clients,
            ROUND(AVG(svc_score)::numeric, 3)    as score_moyen,
            SUM(CASE WHEN alert_level = 'CRITIQUE' THEN 1 ELSE 0 END) as nb_critiques,
            SUM(CASE WHEN alert_level = 'MODEREE'  THEN 1 ELSE 0 END) as nb_moderees,
            SUM(CASE WHEN alert_level = 'NORMAL'   THEN 1 ELSE 0 END) as nb_normaux,
            ROUND(AVG(processing_time_ms)::numeric, 2) as latence_moy_ms
        FROM gold_scores
    """)

    stats = dict(cursor.fetchone())
    conn.close()

    return {
        "dashboard": stats,
        "objectif_latence_ms": 500,
        "latence_ok": stats['latence_moy_ms'] < 500 if stats['latence_moy_ms'] else True
    }

# ============================================================
# ENDPOINT 8 — TEST NOTIFICATION
# POST /notify/test
# ============================================================

@app.post("/notify/test")
def notify_test():
    """
    Tester les notifications (email/SMS)
    """
    return {
        "status": "ok",
        "message": "Notification test envoyee",
        "details": "Configure Twilio et SendGrid dans .env"
    }