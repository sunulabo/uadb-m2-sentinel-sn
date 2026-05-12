from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'equipe02',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Obtention du chemin absolu du projet pour exécuter les scripts correctement
PROJECT_ROOT = os.environ.get('SENTINEL_ROOT', '/opt/airflow/project')

with DAG(
    'sentinel_pipeline',
    default_args=default_args,
    description='Pipeline automatisé Ingestion -> ML pour Sentinel-SN',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['sentinel', 'ml', 'ingestion'],
) as dag:

    # Étape 1 : Simulation / Ingestion (Normalement géré en continu par Kafka, mais on peut simuler un batch ou valider)
    ingestion_check = BashOperator(
        task_id='check_ingestion_data',
        bash_command=f'echo "Vérification des données d\'ingestion dans le datalake HDFS..."',
    )

    # Étape 2 : Entraînement du modèle ML et génération des scores/graphiques
    train_model = BashOperator(
        task_id='train_prediction_model',
        bash_command=f'cd {PROJECT_ROOT}/scripts && python3 train_model.py',
    )

    # Étape 3 : Mise à jour du Dashboard (ex: rafraîchissement d'un cache ou log)
    update_dashboard = BashOperator(
        task_id='update_dashboard_data',
        bash_command=f'echo "Mise à jour des métadonnées du Dashboard et notification prête."',
    )

    # Définition des dépendances d'orchestration
    ingestion_check >> train_model >> update_dashboard
