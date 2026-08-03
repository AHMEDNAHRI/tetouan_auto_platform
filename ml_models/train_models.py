import psycopg2
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Connexion PostgreSQL...")

# ============================================================
# CONNEXION BDD
# ============================================================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="tetouan_auto",
        user="admin",
        password="admin123"
    )

conn = get_connection()

query = """
SELECT 
    c1_frequence, c2_anciennete, c3_valeur,
    c4_sav_mobilite, c5_delai, c6_lstm, alert_level
FROM gold_scores;
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"Lignes recuperees : {len(df)}")

if len(df) < 50:
    print("Pas assez de donnees.")
    exit()

# ============================================================
# PREPARATION DONNEES
# ============================================================

df['alert_level'] = df['alert_level'].map({
    'NORMAL': 0,
    'MODEREE': 1,
    'CRITIQUE': 2
})
df = df.dropna(subset=['alert_level'])

FEATURES = [
    'c1_frequence', 'c2_anciennete', 'c3_valeur',
    'c4_sav_mobilite', 'c5_delai', 'c6_lstm'
]

X = df[FEATURES].fillna(0)
y = df['alert_level'].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train : {len(X_train)} | Test : {len(X_test)}")

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Tetouan_Auto_SVC")

# ============================================================
# MODELE 1 — RANDOM FOREST
# ============================================================

print("\nEntrainement Random Forest...")

with mlflow.start_run(run_name="RandomForest_SVC"):

    rf_params = {
        "n_estimators": 150,
        "max_depth": 10,
        "random_state": 42
    }

    rf_model = RandomForestClassifier(**rf_params)
    rf_model.fit(X_train, y_train)

    rf_preds = rf_model.predict(X_test)
    rf_accuracy = accuracy_score(y_test, rf_preds)

    mlflow.log_params(rf_params)
    mlflow.log_metric("accuracy", rf_accuracy)

    joblib.dump(rf_model, "rf_model.pkl")
    mlflow.log_artifact("rf_model.pkl")

    print(f"Random Forest Accuracy : {rf_accuracy:.4f}")

# ============================================================
# MODELE 2 — MLP
# ============================================================

print("\nEntrainement MLP...")

with mlflow.start_run(run_name="MLP_SVC"):

    mlp_params = {
        "hidden_layer_sizes": (64, 32),
        "activation": "relu",
        "max_iter": 300,
        "random_state": 42
    }

    mlp_model = MLPClassifier(**mlp_params)
    mlp_model.fit(X_train, y_train)

    mlp_preds = mlp_model.predict(X_test)
    mlp_accuracy = accuracy_score(y_test, mlp_preds)

    mlflow.log_params(mlp_params)
    mlflow.log_metric("accuracy", mlp_accuracy)

    joblib.dump(mlp_model, "mlp_model.pkl")
    mlflow.log_artifact("mlp_model.pkl")

    print(f"MLP Accuracy : {mlp_accuracy:.4f}")

# ============================================================
# MODELE 3 — K-MEANS SEGMENTATION
# ============================================================

print("\nSegmentation K-Means...")

conn2 = get_connection()

query_kmeans = """
SELECT 
    client_id,
    AVG(c1_frequence) as freq_moy,
    AVG(c3_valeur)    as valeur_moy,
    AVG(c5_delai)     as delai_moy,
    COUNT(*)          as nb_events
FROM gold_scores
GROUP BY client_id
"""

df_kmeans = pd.read_sql(query_kmeans, conn2)
conn2.close()

if len(df_kmeans) >= 4:

    scaler = StandardScaler()
    features_km = ['freq_moy', 'valeur_moy', 'delai_moy', 'nb_events']
    X_km = scaler.fit_transform(df_kmeans[features_km].fillna(0))

    with mlflow.start_run(run_name="KMeans_Segmentation"):

        km = KMeans(n_clusters=4, random_state=42, n_init=10)
        km.fit(X_km)

        df_kmeans['cluster'] = km.labels_

        cluster_stats = df_kmeans.groupby('cluster').agg({
            'freq_moy': 'mean',
            'valeur_moy': 'mean',
            'delai_moy': 'mean'
        })

        segment_map = {}
        for cluster_id in range(4):
            stats = cluster_stats.loc[cluster_id]
            freq = stats['freq_moy']
            valeur = stats['valeur_moy']
            delai = stats['delai_moy']

            if valeur > cluster_stats['valeur_moy'].mean() and freq > cluster_stats['freq_moy'].mean():
                segment_map[cluster_id] = 'VIP'
            elif delai > cluster_stats['delai_moy'].mean():
                segment_map[cluster_id] = 'INACTIF'
            elif freq > cluster_stats['freq_moy'].mean():
                segment_map[cluster_id] = 'REGULIER'
            else:
                segment_map[cluster_id] = 'OCCASIONNEL'

        df_kmeans['segment'] = df_kmeans['cluster'].map(segment_map)

        mlflow.log_metric("n_clusters", 4)
        mlflow.log_metric("n_clients", len(df_kmeans))

        joblib.dump(km, "kmeans_model.pkl")
        joblib.dump(scaler, "kmeans_scaler.pkl")
        mlflow.log_artifact("kmeans_model.pkl")

        print("\nSegments K-Means :")
        print(df_kmeans['segment'].value_counts())

else:
    print("Pas assez de clients pour K-Means")

# ============================================================
# RESUME FINAL
# ============================================================

joblib.dump(rf_model, "svc_model.pkl")

print("\n" + "="*50)
print("RESUME FINAL — SEMAINE 4")
print("="*50)
print(f"  Random Forest : {rf_accuracy:.4f}")
print(f"  MLP           : {mlp_accuracy:.4f}")
print("  K-Means       : OK")
print(f"  MLflow UI     : http://localhost:5000")
print("="*50)