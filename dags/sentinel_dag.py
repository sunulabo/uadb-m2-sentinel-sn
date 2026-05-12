# dags/sentinel_dag.py — DAG Airflow Sentinel-SN
# Équipe 02 | FALL Ahmed | UADB 2025-2026
# Basé sur sentinel_retrain_dag.py — section 2.5 du sujet

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator      # Airflow 2.6+
from airflow.utils.dates import days_ago
from datetime import timedelta
import subprocess
import logging

logger = logging.getLogger('sentinel_dag')

# ── Arguments par défaut ───────────────────────────────────
default_args = {
    'owner':            'fall_ahmed',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}

# ── T1 : Vérifier nouveaux cas ─────────────────────────────
def check_new_cases(**ctx):
    """
    Vérifie si de nouveaux cas existent dans HBase.
    Branche vers recalculate_thresholds ou skip_retrain.
    """
    try:
        import happybase
        conn = happybase.Connection('hbase', port=9090, timeout=10000)
        conn.open()
        table = conn.table(b'epidemio:cas')
        count = sum(1 for _ in table.scan())
        conn.close()

        logger.info(f'Nombre de cas trouvés : {count}')
        ctx['ti'].xcom_push(key='nb_cas', value=count)

        return 'recalculate_thresholds' if count > 0 else 'skip_retrain'

    except Exception as e:
        logger.error(f'Erreur HBase : {e}')
        return 'skip_retrain'


# ── T2 : Recalculer les seuils ─────────────────────────────
def recalculate_thresholds(**ctx):
    """
    Recalcule les seuils d'alerte par district et maladie.
    Formule : seuil_alerte = AVG(cas) + 2 * STDDEV(cas)
    """
    import happybase
    import statistics

    conn = happybase.Connection('hbase', port=9090, timeout=10000)
    conn.open()

    table_cas    = conn.table(b'epidemio:cas')
    table_seuils = conn.table(b'epidemio:seuils')

    # Regrouper les cas par district + maladie
    donnees = {}
    for _, data in table_cas.scan():
        district = data.get(b'info:district_id', b'0').decode()
        maladie  = data.get(b'info:maladie_code', b'INCONNU').decode()
        nb_cas   = int(data.get(b'stats:nombre_cas', b'0').decode())
        cle      = f'{district}_{maladie}'
        donnees.setdefault(cle, []).append(nb_cas)

    # Calculer et stocker les seuils
    for cle, valeurs in donnees.items():
        moyenne = statistics.mean(valeurs)
        ecart   = statistics.stdev(valeurs) if len(valeurs) >= 2 else 0
        seuil_alerte = moyenne + 2 * ecart
        seuil_moyen  = moyenne

        table_seuils.put(cle.encode(), {
            b'seuil:seuil_moyen':  str(round(seuil_moyen, 2)).encode(),
            b'seuil:seuil_alerte': str(round(seuil_alerte, 2)).encode(),
            b'seuil:date_calcul':  b'2025-08-15',
        })
        logger.info(f'Seuil — {cle} : moy={seuil_moyen:.1f} alerte={seuil_alerte:.1f}')

    conn.close()
    logger.info('Seuils recalculés ✓')


# ── T3 : Mettre à jour le modèle ML ────────────────────────
def update_model(**ctx):
    """
    Lance le script train_model.py via spark-submit.
    En cas d'échec, lève une exception pour Airflow.
    """
    result = subprocess.run(
        [
            'spark-submit',
            '--master', 'spark://spark-master:7077',
            '/opt/spark-apps/models/train_model.py',
            '--output-path', '/opt/spark-apps/models/isolation_forest_latest',
            '--window-days', '30'
        ],
        capture_output=True,
        text=True,
        timeout=1800
    )

    if result.returncode != 0:
        logger.error(f'Spark job échoué : {result.stderr}')
        raise Exception(f'Entraînement échoué : {result.stderr[:200]}')

    logger.info('Modèle mis à jour ✓')
    logger.info(result.stdout[-300:])


# ── Définition du DAG ──────────────────────────────────────
with DAG(
    dag_id='sentinel_equipe02',
    default_args=default_args,
    description='Pipeline Sentinel-SN Équipe 02 — Ingestion → Seuils → ML',
    schedule_interval='0 2 * * 1',   # chaque lundi à 2h
    start_date=days_ago(1),
    catchup=False,
    tags=['sentinel', 'equipe02', 'epidemio', 'mlops']
) as dag:

    start = EmptyOperator(task_id='start')
    skip  = EmptyOperator(task_id='skip_retrain')
    end   = EmptyOperator(
        task_id='end',
        trigger_rule='none_failed_min_one_success'
    )

    t1 = BranchPythonOperator(
        task_id='check_new_cases',
        python_callable=check_new_cases,
        provide_context=True
    )
    t2 = PythonOperator(
        task_id='recalculate_thresholds',
        python_callable=recalculate_thresholds,
        provide_context=True
    )
    t3 = PythonOperator(
        task_id='update_model',
        python_callable=update_model,
        provide_context=True
    )

    # ── Ordre d'exécution (section 2.5 du sujet) ──────────
    # start → t1 → t2 → t3 → end
    #          └→ skip ──────→ end
    start >> t1 >> [t2, skip]
    t2 >> t3 >> end
    skip >> end