#!/bin/bash
# init_hdfs.sh — Initialisation des répertoires HDFS (Sentinel-SN, Équipe 02)
# À exécuter UNE SEULE FOIS après le premier démarrage du NameNode
#
# Usage :
#   chmod +x scripts/init_hdfs.sh
#   ./scripts/init_hdfs.sh

set -e

echo "=================================================="
echo "  Sentinel-SN — Initialisation HDFS"
echo "=================================================="

echo ""
echo "[1/4] Attente que le NameNode soit prêt..."
until docker exec sentinel_namenode hdfs dfs -ls / &>/dev/null; do
  echo "   NameNode pas encore prêt, attente 5s..."
  sleep 5
done
echo "✅ NameNode opérationnel."

echo ""
echo "[2/4] Création de l'arborescence des répertoires..."
docker exec sentinel_namenode bash -c "
  hdfs dfs -mkdir -p /user/equipe02/sentinel_data/analytics &&
  hdfs dfs -mkdir -p /user/equipe02/sentinel_data/raw &&
  hdfs dfs -mkdir -p /user/equipe02/logs
"
echo "✅ Répertoires créés."

echo ""
echo "[3/4] Définition des permissions (groupe equipe02)..."
docker exec sentinel_namenode bash -c "
  hdfs dfs -chown -R nifi:equipe02 /user/equipe02 2>/dev/null || true
  hdfs dfs -chmod -R 755 /user/equipe02
"
echo "✅ Permissions définies."

echo ""
echo "[4/4] Vérification de l'arborescence :"
docker exec sentinel_namenode hdfs dfs -ls -R /user/equipe02

echo ""
echo "=================================================="
echo "✅ HDFS initialisé avec succès !"
echo ""
echo "  Interface Web HDFS : http://localhost:9870"
echo "  Chemin analytics   : hdfs://namenode:9000/user/equipe02/sentinel_data/analytics/"
echo "=================================================="
