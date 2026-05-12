-- hive_schema.sql — Tables Hive pour Sentinel-SN (Équipe 02)
-- Partitionnement optimisé : annee/mois/region (recommandation audit Data Architect)
-- Format : PARQUET + SNAPPY (colonnaire, compression ~70%)

CREATE DATABASE IF NOT EXISTS equipe02_sentinel_db;

USE equipe02_sentinel_db;

-- ─── Table principale analytique ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS sentinel_analytics (
    id_patient        STRING   COMMENT 'Hash HMAC-SHA256 anonymisé (64 chars)',
    date_consultation TIMESTAMP,
    age               INT,
    sexe              STRING,
    code_pathologie   STRING   COMMENT 'PALU | GRIPPE | DENGUE | CHOLERA',
    temperature       FLOAT
)
PARTITIONED BY (
    annee  INT    COMMENT 'Année de consultation (partitionnement primaire)',
    mois   INT    COMMENT 'Mois de consultation (partitionnement secondaire)',
    region STRING COMMENT 'Région Sénégal (Dakar, Saint-Louis, Ziguinchor, Touba, Thies)'
)
STORED AS PARQUET
LOCATION '/user/equipe02/sentinel_data/analytics'
TBLPROPERTIES (
    'parquet.compression'        = 'SNAPPY',
    'creator'                    = 'equipe02',
    'parquet.block.size'         = '134217728',  -- 128MB par bloc (optimal HDFS)
    'hive.exec.dynamic.partition'= 'true'
);

-- ─── Exemple de requête analytique optimisée ────────────────────────────────
-- Lecture d'un seul mois + région → scan minimal (2 partitions sur 3 niveaux)
--
-- SELECT code_pathologie, COUNT(*) AS nb_cas, ROUND(AVG(temperature), 2) AS temp_moy
-- FROM equipe02_sentinel_db.sentinel_analytics
-- WHERE annee = 2026 AND mois = 5 AND region = 'Dakar'
-- GROUP BY code_pathologie
-- ORDER BY nb_cas DESC;

-- ─── Enregistrement des nouvelles partitions après écriture NiFi ─────────────
-- Exécuter après chaque batch d'écriture HDFS :
-- MSCK REPAIR TABLE sentinel_analytics;

-- ─── Structure des répertoires HDFS attendue par NiFi ────────────────────────
-- /user/equipe02/sentinel_data/analytics/annee=2026/mois=5/region=Dakar/
-- /user/equipe02/sentinel_data/analytics/annee=2026/mois=5/region=Thies/
-- /user/equipe02/sentinel_data/analytics/annee=2026/mois=6/region=Dakar/
