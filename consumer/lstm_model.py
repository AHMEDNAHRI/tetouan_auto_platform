# consumer/lstm_model.py

import numpy as np
import psycopg2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# CONNEXION POSTGRES
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
# HISTORIQUE CLIENT
# ============================================================

def get_client_history(client_id: int, n_events: int = 30):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            amount,
            EXTRACT(EPOCH FROM (NOW() - timestamp)) / 86400 as days_ago
        FROM bronze_events
        WHERE client_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """, (client_id, n_events))

    rows = cursor.fetchall()
    conn.close()

    return rows


# ============================================================
# SCORE LSTM (UTILISÉ PAR CONSUMER)
# ============================================================

def compute_lstm_score(client_id: int) -> float:

    history = get_client_history(client_id)

    if len(history) < 5:
        return 0.3

    # ✅ CONVERSION EN FLOAT (CORRECTION PRINCIPALE)
    amounts  = [float(row[0]) for row in history]
    days_ago = [float(row[1]) for row in history]

    max_amount = max(amounts)  + 1e-8
    max_days   = max(days_ago) + 1e-8

    amounts_norm = np.array(amounts)  / max_amount
    days_norm    = np.array(days_ago) / max_days

    # Calcul dérive
    recent_activity = np.mean(days_norm[:5])
    old_activity    = np.mean(days_norm[-5:]) if len(days_norm) >= 10 else recent_activity

    drift_score = recent_activity / (old_activity + 1e-8)
    drift_score = float(np.clip(drift_score, 0, 1))

    return drift_score


# ============================================================
# MODELE LSTM
# ============================================================

def build_lstm_model():

    model = Sequential([
        LSTM(32, input_shape=(30, 2), return_sequences=False),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model


# ============================================================
# ENTRAINEMENT LSTM
# ============================================================

def train_lstm_model():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT client_id
        FROM bronze_events
        GROUP BY client_id
        HAVING COUNT(*) >= 5
    """)

    client_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if len(client_ids) < 10:
        print("Pas assez de clients pour entrainer LSTM")
        return None

    print(f"Entrainement LSTM sur {len(client_ids)} clients...")

    X, y = [], []

    for client_id in client_ids:

        history = get_client_history(client_id)
        if len(history) < 5:
            continue

        # ✅ CONVERSION EN FLOAT
        amounts  = [float(row[0]) for row in history]
        days_ago = [float(row[1]) for row in history]

        max_amount = max(amounts)  + 1e-8
        max_days   = max(days_ago) + 1e-8

        amounts_norm = np.array(amounts)  / max_amount
        days_norm    = np.array(days_ago) / max_days

        sequence = np.column_stack([amounts_norm, days_norm])

        # Pad à 30
        if len(sequence) < 30:
            padding  = np.zeros((30 - len(sequence), 2))
            sequence = np.vstack([padding, sequence])
        else:
            sequence = sequence[:30]

        X.append(sequence)

        # Label churn
        label = 1 if days_ago[0] > 30 else 0
        y.append(label)

    if len(X) < 10:
        print("Pas assez de donnees pour LSTM")
        return None

    X = np.array(X)
    y = np.array(y)

    model = build_lstm_model()

    model.fit(
        X, y,
        epochs=10,
        batch_size=8,
        validation_split=0.2,
        verbose=1
    )

    print("LSTM entraine avec succes !")

    model.save("lstm_model.h5")
    print("LSTM sauvegarde : lstm_model.h5")

    return model


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    train_lstm_model()