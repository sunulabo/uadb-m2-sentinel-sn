# 🛡️ Sentinel-SN (UADB - Master 2 Big Data)
**Santé & Alerte Épidémiologique — Projet M2 Big Data UADB 2025-2026**

**Equipe 02 :**
- SALL Abou Bacre (Étudiant 1)
- FALL Ahmed (Étudiant 2)

---

## 🏗️ Architecture du Projet (ASCII Art)

```text
       [ SIMULATEUR ]                          [ ORCHESTRATION ]
      scripts/kafka_producer.py                dags/sentinel_dag.py (Airflow)
               |                                        |
               | (JSON)                                 v
               v                           +-------------------------+
       +---------------+                   |     ML & PREDICTION     |
       |     KAFKA     |                   | scripts/train_model.py  |
       | (Topic:       |                   +-------------------------+
       | equipe02_...) |                                ^
       +---------------+                                | (Lecture Modèle/Parquet)
               |                                        |
               | (Streaming)                            v
               v                           +-------------------------+
       +---------------+                   |   DASHBOARD & ALERTE    |
       |  APACHE NIFI  |                   | dashboard_app.py        |
       | (Anonymisation|                   | (Streamlit)             |
       |  & Parquet)   |                   +-------------------------+
       +---------------+
               |
               | (Stockage)
               v
       +-----------------------+
       | HDFS / HIVE / HBASE   |
       | (Partition by Region) |
       +-----------------------+
```

## 🚀 Fonctionnalités Principales

1. **Ingestion & Streaming (S1)** : Génération de données synthétiques validées par Pandera et poussées vers un cluster Kafka KRaft.
2. **Stockage & Privacy (S2)** : Traitement via NiFi, anonymisation des patients (SHA-256), et stockage au format Parquet (HDFS) avec table externe Hive partitionnée.
3. **Machine Learning (S3)** : Entraînement d'un modèle `RandomForest` pour prédire la température, évaluation (RMSE/R²), et DAG Airflow d'automatisation.
4. **Dashboarding (S3)** : Interface Streamlit pour la visualisation des performances et la prédiction interactive.

## 🛠️ Installation & Démarrage

### 1. Lancement de l'infrastructure Docker
```bash
cd docker
docker-compose up -d
```

### 2. Installation des dépendances Python
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Exécution du Simulateur Kafka
```bash
python scripts/kafka_producer.py
```

### 4. Lancement du Dashboard (Streamlit)
```bash
cd dashboard
streamlit run dashboard_app.py
```

## 📜 Conventions
- **Base de données/Topics** : Préfixe `equipe02_`
- **Commits** : Format `[Sx] type: description`
