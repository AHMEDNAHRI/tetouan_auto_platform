# 🚗 Plateforme d’Intelligence Commerciale Temps Réel  
## Tetouan Automobile — Ventes, SAV & RentopCar (LCD/LLD)

### 👨‍🎓 Réalisé par
Ahmed NAHRI  
4ème Année — Ingénierie IA & Data  
EMSI Tanger — 2026  

---

# 📌 1. Contexte & Problématique

Tetouan Automobile (Concessionnaire officiel Renault & Dacia) dispose de 3 pôles d’activité :

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
- Générer des alertes automatiques
- Fournir des dashboards opérationnels et managériaux

---

# 🏗 2. Architecture Technique

### 🔁 Pipeline Temps Réel

Simulateur Python  
→ Apache Kafka  
→ Consumer Python (SVC < 500ms)  
→ PostgreSQL (Bronze / Silver / Gold)  
→ LSTM + Random Forest + MLP  
→ Grafana + Power BI  
→ FastAPI REST  
→ Apache Airflow (orchestration)

---

## 🧰 Technologies Utilisées

| Outil | Rôle |
|--------|------|
| Docker | Conteneurisation complète |
| Apache Kafka | Streaming temps réel |
| PostgreSQL | ETL Bronze/Silver/Gold |
| Random Forest | Détection churn (82%) |
| MLP | Meilleur modèle (91%) |
| LSTM | Détection dérive comportementale |
| K-Means | Segmentation (VIP / Régulier / Occasionnel / Inactif) |
| MLflow | Tracking des modèles |
| FastAPI | API REST |
| Grafana | Dashboard temps réel |
| Power BI | Reporting management |
| Apache Airflow | Orchestration automatique |

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

## 🎨 Niveaux d’Alerte

| Score | Niveau | Action |
|--------|--------|--------|
| < 0.50 | ✅ Normal | Aucune action |
| 0.50 – 0.75 | 🟠 Modéré | Offre ciblée |
| ≥ 0.75 | 🔴 Critique | Relance urgente |

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
| Random Forest | 82% |
| MLP | ✅ 91% |
| LSTM | Détection dérive progressive |

Tracking via MLflow.

---

# 🔐 8. Sécurité & Bonnes Pratiques

- Secrets externalisés via variables d’environnement
- .env non versionné
- Architecture conteneurisée
- Données simulées (conformité loi 09‑08)

---

# ▶️ 9. Lancer le Projet

```bash
docker-compose up -d

# 10. Accès aux Services
service:Grafana
url:http://localhost:3000
Description:Dashboard temps réel

service:Airflow
url:http://localhost:8080
Description:Orchestration des pipelines

service:MLflow
url:http://localhost:5000
Description:Suivi des modèles IA

service:FastAPI
url:http://localhost:8000/docs
Description:Documentation API Swagger

service:PostgreSQL
url:localhost:5433
Description:Base de données ETL

service:Kafka
url:localhost:9092
Description:Broker de streaming

# 11. Résultats Obtenus
✅ Pipeline Kafka fonctionnel
✅ Score SVC calculé en < 500 ms
✅ 4 segments clients intelligents
✅ Alertes automatiques en temps réel
✅ Dashboards opérationnels
✅ Architecture industrialisable

# 12.Valeur Ajoutée pour Tetouan Automobile

Avant: Données cloisonnées
Apres: 	Vue 360° client

Avant: Pas de détection churn
Apres: Alertes automatiques

Avant: Décisions intuitives
Apres: IA (91% précision)

Avant: Pas de segmentation
Apres: 4 segments intelligents

Avant: Pas de dashboard centralisé
Apres: Grafana + Power BI