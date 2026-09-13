# 🚗 Plateforme d'Intelligence Commerciale Temps Réel  
## Tetouan Automobile — Ventes, SAV & RentopCar (LCD/LLD)

### 👨‍🎓 Réalisé par
Ahmed NAHRI  
4ème Année — Ingénierie IA & Data  
EMSI Tanger — 2026  

---

# 📌 1. Contexte & Problématique

Tetouan Automobile (Concessionnaire officiel Renault & Dacia) dispose de 3 pôles d'activité :

- ✅ Ventes de véhicules
- ✅ Service Après-Vente (SAV)
- ✅ Location Courte et Longue Durée (RentopCar)

Actuellement :

- Les données sont cloisonnées
- Aucune détection précoce de churn
- Pas de vue 360° client
- Décisions basées sur intuition

🎯 Objectif du projet :

Développer une **plateforme temps réel** capable de :

- Unifier les données Ventes + SAV + Location
- Calculer un Score Valeur Client (SVC)
- Détecter le risque de churn
- Générer des alertes automatiques (dashboard + email)
- Fournir des dashboards opérationnels et managériaux

---

# 🏗 2. Architecture Technique — Schéma du Pipeline

```
+-----------------------------------------------------------------+
|                ENVIRONNEMENT LOCAL : CONTENEUR DOCKER           |
|                                                                   |
|                 APACHE AIRFLOW (Chef d'orchestre)                |
|                                                                   |
|  E - EXTRACTION (3 sources unifiées)                             |
|  Simulateur Python (schéma réel Tetouan Automobile)              |
|  - Ventes    : clients, cars, bax_commandes                      |
|  - SAV       : charges, car_accidents, payments                  |
|  - RentopCar : car_rentals (LCD/LLD), car_rental_invoices         |
|                    -> Kafka Producer                              |
|                    -> Kafka Broker                                |
|                    -> Kafka Consumer                              |
|                            |                                      |
|                            v                                      |
|  T - TRANSFORMATION (Boucle Critique <= 500ms)                   |
|  Matrice X(t)          -> NumPy                                   |
|  Normalisation Z(t)    -> scikit-learn                            |
|  Fonction SVC          -> NumPy (6 composantes enrichies)         |
|  RF + MLP + KNN + Reg. Logistique + XGBoost + Gradient Boosting   |
|                         -> MLflow + scikit-learn + XGBoost         |
|  Decision finale        -> Python                                 |
|                            |                                      |
|                            v                                      |
|  L - LOAD (Ecriture Asynchrone)                                  |
|  Bronze -> evenements bruts        -> PostgreSQL                  |
|  Silver -> donnees nettoyees       -> PostgreSQL                  |
|  Gold   -> scores SVC + alertes    -> PostgreSQL                  |
|  LSTM   -> analyse tendances       -> Keras                       |
+====================================|==============================+
                                      |
                +---------------------+---------------------+
                v                                             v
+---------------------------+                +---------------------------+
|  RESTITUTION VISU         |                |  RESTITUTION API           |
|  Grafana   (5s)           |                |  FastAPI REST               |
|  Power BI  (60s)          |                |  Swagger UI                 |
+---------------------------+                +--------------|-------------+
                                                              v
                                              +---------------------------+
                                              |  TUNNEL SECURISE            |
                                              |  Ngrok / Serveo             |
                                              |  Encadrant                   |
                                              |  Tetouan Auto                |
                                              +--------------|-------------+
                                                              v
                                              +---------------------------+
                                              |  NOTIFICATIONS & FEEDBACK   |
                                              |  Gmail API (alertes auto)   |
                                              |  Email Encadrant/Directeur  |
                                              |  Feedback Loop (retour      |
                                              |  humain -> réentraînement)  |
                                              +---------------------------+
```

---

## 🧰 Technologies Utilisées

| Outil | Rôle |
|--------|------|
| Docker | Conteneurisation complète |
| Apache Kafka | Streaming temps réel |
| PostgreSQL | ETL Bronze/Silver/Gold |
| Random Forest | Détection churn (0.9036) |
| MLP | Détection churn (0.9877) |
| LSTM | Détection dérive comportementale |
| KNN | Modèle de classification (0.9109) |
| Régression Logistique | ✅ Meilleur modèle (0.9936) |
| XGBoost | Modèle de boosting (0.9313) |
| Gradient Boosting | Modèle de boosting (0.9300) |
| K-Means | Segmentation (VIP / Régulier / Occasionnel / Inactif) |
| MLflow | Tracking des modèles |
| FastAPI | API REST |
| Grafana | Dashboard temps réel |
| Power BI | Reporting management |
| Apache Airflow | Orchestration automatique |
| Ngrok / Serveo | Tunnel sécurisé pour exposer l'API/dashboard |
| Gmail API | Notifications automatiques par email |

---

# ⚙️ 3. Fonctionnement du Système

## 🔄 4 Boucles Temporelles

1️⃣ Kafka (toutes les 5 secondes)  
2️⃣ Boucle critique (≤ 500 ms)  
3️⃣ LSTM (analyse 30 derniers événements)  
4️⃣ Restitution (60 secondes)

---

# 🧮 4. Score Valeur Client (SVC)

Le SVC ∈ [0,1] est calculé à partir de 6 composantes :

- C1 : Fréquence achat/location
- C2 : Ancienneté client
- C3 : Valeur monétaire totale
- C4 : Historique SAV & mobilité
- C5 : Délai dernier contact
- C6 : Dérive LSTM

Formule :

S(t) = Sigmoïde(Σ wi * Zi)

---

## 🎨 Niveaux d'Alerte

| Score | Niveau | Action |
|--------|--------|--------|
| < 0.50 | ✅ Normal | Aucune action |
| 0.50 – 0.75 | 🟠 Modéré | Offre ciblée + email de notification |
| ≥ 0.75 | 🔴 Critique | Relance urgente + email immédiat au directeur/encadrant |

---

# 🗄 5. Modèle de Données (Architecture Medallion)

## Bronze
Données brutes Kafka

## Silver
Données nettoyées + normalisées

## Gold
Scores SVC + Alertes + Décisions

---

# 📊 6. Dashboards

## 🔹 Grafana
- Alertes en temps réel
- Top clients critiques
- Volume événements
- Performance système

## 🔹 Power BI
- KPIs LCD / LLD / SAV / CA
- Segmentation K-Means
- Heatmap churn
- Recommandations commerciales

---

# 🧠 7. Intelligence Artificielle

| Modèle | Performance |
|--------|------------|
| Random Forest | 0.9036 |
| MLP | 0.9877 |
| KNN | 0.9109 |
| Régression Logistique | ✅ 0.9936 (meilleur modèle) |
| Gradient Boosting | 0.9300 |
| XGBoost | 0.9313 |
| K-Means | OK (segmentation validée) |
| LSTM | Détection dérive progressive |

Tous les modèles sont trackés et comparés via **MLflow** (métriques, hyperparamètres, versions).

---

# 📧 8. Notifications Gmail Automatiques & Feedback Loop

## 🔔 Notifications Gmail
- Envoi automatique d'un email via l'API Gmail dès qu'un client atteint un score **Modéré** ou **Critique**
- Destinataires : Directeur / Encadrant Tetouan Automobile
- Contenu : score du client, niveau d'alerte, historique résumé, action recommandée

## 🔁 Feedback Loop
- L'encadrant/directeur peut valider, corriger ou rejeter une alerte reçue
- Ce retour humain est réinjecté dans le pipeline pour améliorer le réentraînement des modèles
- Objectif : réduire les faux positifs et affiner le SVC au fil du temps

---

# 🔐 9. Sécurité & Bonnes Pratiques

- Secrets externalisés via variables d'environnement
- .env non versionné
- Architecture conteneurisée
- Données simulées (conformité loi 09‑08)
- Exposition sécurisée des services locaux (API/Dashboard) via **tunnel Ngrok ou Serveo**
- Accès restreint pour l'encadrant et Tetouan Automobile uniquement

---

# ▶️ 10. Lancer le Projet

```bash
docker-compose up -d
```

# 11. Accès aux Services

service: Grafana
url: http://localhost:3000
Description: Dashboard temps réel

service: Airflow
url: http://localhost:8080
Description: Orchestration des pipelines

service: MLflow
url: http://localhost:5000
Description: Suivi des modèles IA

service: FastAPI
url: http://localhost:8000/docs
Description: Documentation API Swagger

service: PostgreSQL
url: localhost:5433
Description: Base de données ETL

service: Kafka
url: localhost:9092
Description: Broker de streaming

service: Ngrok / Serveo
url: (généré dynamiquement au lancement)
Description: Tunnel sécurisé pour exposer l'API/Dashboard à l'extérieur

---

# 📸 12. Captures d'écran

<!-- Placez vos images dans un dossier /screenshots à la racine du repo avec exactement ces noms de fichiers -->

### 🎲 Simulateur & Ingestion des données

| Génération des événements (Simulateur) | Réception côté Consumer Kafka |
|---|---|
| ![Simulateur](screenshots/simulateur-generation.png) | ![Consumer](screenshots/recu-consumer.png) |

| Modèles Docker |
|---|
| ![Docker Models](screenshots/docker-models.png) |

### 🔄 Orchestration — Apache Airflow

| Connexion Airflow | Page d'accueil Airflow |
|---|---|
| ![Airflow Login](screenshots/airflow-login.png) | ![Airflow Home](screenshots/airflow-home.png) |

| Graphe du DAG | Vue Gantt |
|---|---|
| ![Airflow Graph](screenshots/airflow-graph.png) | ![Airflow Gantt](screenshots/airflow-gantt.png) |

| Détails d'exécution |
|---|
| ![Airflow Details](screenshots/airflow-details.png) |

### 🧠 Suivi des modèles IA — MLflow

| Page d'accueil MLflow | Détails d'une expérimentation |
|---|---|
| ![MLflow Home](screenshots/mlflow-home.png) | ![MLflow Experiment](screenshots/mlflow-experiment.png) |

| Comparaison des modèles | Analyse du churn |
|---|---|
| ![Comparaison Modèles](screenshots/comparaison-models.png) | ![Analyse Churn](screenshots/analyse-churn.png) |

| Segmentation K-Means |
|---|
| ![Segmentation K-Means](screenshots/segmentation-kmeans.png) |

### 📊 Dashboards — Grafana & Power BI

| Connexion Grafana | Page d'accueil Grafana |
|---|---|
| ![Grafana Login](screenshots/grafana-login.png) | ![Grafana Home](screenshots/grafana-home.png) |

| Dashboard principal | Vue Executive Overview |
|---|---|
| ![Dashboard Grafana](screenshots/dashboard-grafana.png) | ![Executive Overview](screenshots/executive-overview.png) |

| Performance RentopCar / SAV | Activation du tunnel sécurisé |
|---|---|
| ![RentopCar SAV Performance](screenshots/rentopcar-sav-performance.png) | ![Activation Tunnel Grafana](screenshots/activation-tunnel-grafana.png) |

| Grafana via le tunnel |
|---|
| ![Grafana via Tunnel](screenshots/grafana-via-tunnel.png) |

### 📧 Notifications & Recommandations

| Accès à un email spécifique | Emails reçus |
|---|---|
| ![Accès Email Spécifique](screenshots/acces-email-specifique.png) | ![Reçu des Emails](screenshots/recu-des-emails.png) |

| Recommandation commerciale |
|---|
| ![Recommandation Commerciale](screenshots/recommendation-commerciale.png) |

---

# 13. Résultats Obtenus
✅ Pipeline Kafka fonctionnel
✅ Score SVC calculé en < 500 ms
✅ 4 segments clients intelligents
✅ 6 modèles IA comparés (RF, MLP, KNN, Reg. Logistique, XGBoost, Gradient Boosting)
✅ Alertes automatiques en temps réel (dashboard + email)
✅ Feedback loop pour amélioration continue des modèles
✅ Dashboards opérationnels
✅ Tunnel sécurisé Ngrok/Serveo
✅ Architecture industrialisable

# 14. Valeur Ajoutée pour Tetouan Automobile

Avant: Données cloisonnées
Après: Vue 360° client

Avant: Pas de détection churn
Après: Alertes automatiques (dashboard + email)

Avant: Décisions intuitives
Après: IA (jusqu'à 99.36% précision, 6 modèles comparés)

Avant: Pas de segmentation
Après: 4 segments intelligents

Avant: Pas de dashboard centralisé
Après: Grafana + Power BI

Avant: Pas de retour humain sur les alertes
Après: Feedback loop pour réentraînement continu