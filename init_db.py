import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="tetouan_auto",
    user="admin",
    password="admin123"
)

cursor = conn.cursor()

# TABLE BRONZE — données brutes
cursor.execute("""
CREATE TABLE IF NOT EXISTS bronze_events (
    id           SERIAL PRIMARY KEY,
    timestamp    TIMESTAMP DEFAULT NOW(),
    client_id    INTEGER,
    event_type   VARCHAR(50),
    car_id       INTEGER,
    amount       DECIMAL(10,2),
    status       VARCHAR(30),
    raw_payload  JSONB
);
""")

# TABLE SILVER — données nettoyées
cursor.execute("""
CREATE TABLE IF NOT EXISTS silver_clients (
    id                  SERIAL PRIMARY KEY,
    timestamp           TIMESTAMP DEFAULT NOW(),
    client_id           INTEGER,
    z_frequence         FLOAT,
    z_anciennete        FLOAT,
    z_valeur            FLOAT,
    z_sav_mobilite      FLOAT,
    z_delai             FLOAT,
    valeur_location_rpd FLOAT,
    is_valid            BOOLEAN
);
""")

# TABLE GOLD — scores et alertes
cursor.execute("""
CREATE TABLE IF NOT EXISTS gold_scores (
    id                 SERIAL PRIMARY KEY,
    timestamp          TIMESTAMP DEFAULT NOW(),
    client_id          INTEGER,
    svc_score          FLOAT,
    alert_level        VARCHAR(20),
    decision           VARCHAR(50),
    c1_frequence       FLOAT,
    c2_anciennete      FLOAT,
    c3_valeur          FLOAT,
    c4_sav_mobilite    FLOAT,
    c5_delai           FLOAT,
    c6_lstm            FLOAT,
    processing_time_ms FLOAT
);
""")

conn.commit()
cursor.close()
conn.close()

print("Tables Bronze, Silver, Gold creees avec succes !")