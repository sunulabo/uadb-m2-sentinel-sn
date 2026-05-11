# hbase_setup.py — Création des tables HBase pour Sentinel-SN
# Équipe 02 | UADB 2025-2026

import happybase
import logging

logger = logging.getLogger('HBaseSetup')


def create_sentinel_tables():
    """Crée le namespace et les tables HBase pour Sentinel-SN."""
    conn = happybase.Connection('localhost', port=9090, timeout=10000)
    conn.open()

    # ── Créer le namespace epidemio s'il n'existe pas ─────
    try:
        conn.client.createNamespace(
            happybase.hbase.ttypes.NamespaceDescriptor(name=b'epidemio')
        )
        logger.info('Namespace epidemio créé ✓')
    except Exception as e:
        logger.info(f'Namespace epidemio déjà existant ou erreur : {e}')

    tables_a_creer = {
        # Table principale : cas épidémiques anonymisés
        b'epidemio:cas': {
            'info':   {'max_versions': 1},
            'stats':  {'max_versions': 5},
            'alerte': {'max_versions': 1},
        },
        # Table alertes temps réel (TTL 7 jours)
        b'epidemio:alertes': {
            'meta':    {'max_versions': 1, 'time_to_live': 604800},
            'payload': {'max_versions': 1, 'time_to_live': 604800},
        },
        # Table seuils par district
        b'epidemio:seuils': {
            'seuil': {'max_versions': 10},
        },
        # Table météo pour corrélation pluie/maladies
        b'epidemio:meteo': {
            'mesure': {'max_versions': 5},
        },
    }

    tables_existantes = [t.decode() for t in conn.tables()]
    logger.info(f'Tables existantes : {tables_existantes}')

    for table_name, families in tables_a_creer.items():
        nom = table_name.decode()
        if nom in tables_existantes:
            logger.info(f'Table {nom} déjà existante — ignorée')
        else:
            conn.create_table(table_name, families)
            logger.info(f'Table {nom} créée avec succès ✓')

    print('\n── Tables HBase Sentinel-SN ──')
    for t in conn.tables():
        print(f'  ✓ {t.decode()}')

    conn.close()
    logger.info('Setup HBase Sentinel-SN terminé')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_sentinel_tables()