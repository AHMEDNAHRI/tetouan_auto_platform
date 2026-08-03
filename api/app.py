# api/app.py
from fastapi import FastAPI
import psycopg2
import json

app = FastAPI(title='Tetouan Auto Intelligence API')

def get_db():
    return psycopg2.connect(
        host="localhost", port="5433",
        database="tetouan_auto",
        user="admin", password="admin123"
    )

@app.get('/health')
def health():
    return {'status': 'ok', 'projet': 'Tetouan Auto'}

@app.get('/scores/latest')
def get_latest_scores():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT client_id, svc_score, alert_level,
               decision, client_segment, timestamp
        FROM gold_scores
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'client_id':   r[0],
            'svc_score':   r[1],
            'alert_level': r[2],
            'decision':    r[3],
            'segment':     r[4],
            'timestamp':   str(r[5])
        }
        for r in rows
    ]

@app.get('/alerts/active')
def get_active_alerts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT client_id, svc_score, alert_level,
               decision, client_segment, timestamp
        FROM gold_scores
        WHERE alert_level IN ('CRITIQUE', 'MODEREE')
        ORDER BY svc_score DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'client_id':   r[0],
            'svc_score':   r[1],
            'alert_level': r[2],
            'decision':    r[3],
            'segment':     r[4],
            'timestamp':   str(r[5])
        }
        for r in rows
    ]

@app.get('/scores/client/{client_id}')
def get_client_score(client_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT client_id, svc_score, alert_level,
               decision, client_segment, timestamp
        FROM gold_scores
        WHERE client_id = %s
        ORDER BY timestamp DESC
        LIMIT 10
    """, (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'client_id':   r[0],
            'svc_score':   r[1],
            'alert_level': r[2],
            'decision':    r[3],
            'segment':     r[4],
            'timestamp':   str(r[5])
        }
        for r in rows
    ]

@app.get('/segments/stats')
def get_segments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT client_segment, COUNT(DISTINCT client_id)
        FROM gold_scores
        GROUP BY client_segment
    """)
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

@app.get('/rentopcar/stats')
def get_rentopcar_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, COUNT(*), AVG(amount)
        FROM bronze_events
        WHERE event_type IN ('LOCATION_LCD', 'LOCATION_LLD')
        GROUP BY event_type
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'type':       r[0],
            'count':      r[1],
            'avg_amount': round(float(r[2]), 2)
        }
        for r in rows
    ]