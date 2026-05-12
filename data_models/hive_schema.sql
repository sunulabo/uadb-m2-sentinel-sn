-- Schéma SQL pour la table externe Hive (Sentinel-SN)

CREATE DATABASE IF NOT EXISTS equipe02_sentinel_db;

USE equipe02_sentinel_db;

CREATE EXTERNAL TABLE IF NOT EXISTS sentinel_analytics (
    id_patient STRING,
    date_consultation TIMESTAMP,
    age INT,
    sexe STRING,
    code_pathologie STRING,
    temperature FLOAT
)
PARTITIONED BY (region STRING)
STORED AS PARQUET
LOCATION '/user/equipe02/sentinel_data/analytics'
TBLPROPERTIES (
    'parquet.compression'='SNAPPY',
    'creator'='equipe02'
);

-- Note : Les données provenant de NiFi doivent être écrites dans des sous-répertoires
-- correspondant aux partitions, ex: /user/equipe02/sentinel_data/analytics/region=Dakar/
-- Ensuite, exécuter la commande suivante pour que Hive reconnaisse les nouvelles partitions :
-- MSCK REPAIR TABLE sentinel_analytics;
