# uadb-m2-sentinel-sn
Santé &amp; Alerte Épidémiologique — Master 2 Big Data UADB 2025-2026
**Ahmed FALL Abou Bacre SALL** | Master 2 DSGL | UADB 2025-2026

## Démarrage rapide

```bash
# 1. Démarrer Docker
docker compose up -d zookeeper
sleep 10
docker compose up -d kafka nifi hbase hive-metastore
sleep 30
docker compose up -d spark-master spark-worker airflow

# 2. Démarrer Thrift HBase
./start_thrift.sh

# 3. Initialiser HBase
python hbase_setup.py

# 4. Lancer le simulateur
python kafka_producer.py

# 5. Lancer le dashboard
python dashboard/dashboard_alertes.py
```

## Interfaces web
- NiFi    : http://localhost:8081
- Spark   : http://localhost:8080
- Airflow : http://localhost:8082 (admin/admin)
- HBase   : http://localhost:16010

## Fichiers importants
- kafka_producer.py       → simule les données
- hbase_setup.py          → crée les tables HBase
- privacy_layer.py        → anonymise les patients
- dags/sentinel_dag.py    → pipeline automatique
- dashboard/dashboard_alertes.py → affiche les alertes
