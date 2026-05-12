#!/bin/bash
# pipeline_start.sh — Lance le pipeline complet Sentinel-SN
# Équipe 02 | FALL Ahmed | UADB 2025-2026

echo "========================================"
echo "  Sentinel-SN | Pipeline Équipe 02"
echo "========================================"

# 1. Vérifier que les services tournent
echo "[1/4] Vérification des services..."
docker compose ps | grep -E "kafka|hbase|airflow"

# 2. Insérer données de test dans HBase
echo "[2/4] Insertion données de test HBase..."
python insert_test_data.py

# 3. Lancer le simulateur Kafka en arrière-plan
echo "[3/4] Démarrage simulateur Kafka..."
python kafka_producer.py &
PRODUCER_PID=$!
echo "Simulateur PID : $PRODUCER_PID"
sleep 10

# 4. Lancer le modèle ML
echo "[4/4] Entraînement du modèle ML..."
python models/train_model.py --output-path models/resultats

echo ""
echo "Pipeline démarré ✓"
echo "Arrêter le simulateur : kill $PRODUCER_PID"