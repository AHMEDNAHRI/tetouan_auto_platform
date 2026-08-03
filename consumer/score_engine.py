import numpy as np
import time

WEIGHTS = [0.20, 0.15, 0.25, 0.15, 0.15, 0.10]

# Valeurs de référence pour normalisation
MEANS = [10.0, 30.0, 4000.0, 0.5, 180.0, 0.5]
STDS  = [5.0,  15.0, 2000.0, 0.3,  90.0, 0.3]

def compute_svc(features: dict) -> dict:
    start = time.time()

    # Etape 1 — Matrice X(t)
    X = np.array([
        features.get('frequence',     0),
        features.get('anciennete',    0),
        features.get('valeur',        0),
        features.get('sav_mobilite',  0),
        features.get('delai_contact', 0),
        features.get('lstm_drift',    0),
    ])

    # Etape 2 — Normalisation Z-score avec références fixes
    Z = (X - np.array(MEANS)) / (np.array(STDS) + 1e-8)

    # Clamp entre -3 et +3
    Z = np.clip(Z, -3, 3)

    # Etape 3 — Score agrege pondere
    A = np.dot(WEIGHTS, Z)

    # Etape 4 — Sigmoide [0, 1]
    S = 1 / (1 + np.exp(-2.5 * (A - 0.0)))

    # Etape 5 — Decision
    if S >= 0.75:
        decision = 'RELANCER'
        alert    = 'CRITIQUE'
    elif S >= 0.50:
        decision = 'FIDELISER'
        alert    = 'MODEREE'
    else:
        decision = 'CONTINUER'
        alert    = 'NORMAL'

    processing_ms = (time.time() - start) * 1000

    return {
        'svc_score':       float(S),
        'decision':        decision,
        'alert_level':     alert,
        'processing_ms':   processing_ms,
        'c1_frequence':    float(Z[0]),
        'c2_anciennete':   float(Z[1]),
        'c3_valeur':       float(Z[2]),
        'c4_sav_mobilite': float(Z[3]),
        'c5_delai':        float(Z[4]),
        'c6_lstm':         float(Z[5]),
    }