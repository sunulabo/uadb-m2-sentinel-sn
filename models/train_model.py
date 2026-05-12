# train_model.py — Modèle de détection d'anomalies épidémiques
# Équipe 02 | UADB 2025-2026

import argparse
import logging
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TrainModel')


def charger_donnees_hbase():
    """Charge les données depuis HBase pour l'entraînement."""
    import happybase

    conn = happybase.Connection('localhost', port=9090, timeout=10000)
    conn.open()
    table = conn.table(b'epidemio:cas')

    donnees = []
    for row_key, data in table.scan():
        try:
            donnees.append({
                'district_id':  int(data.get(b'info:district_id',  b'0').decode()),
                'maladie_code': data.get(b'info:maladie_code', b'INCONNU').decode(),
                'nombre_cas':   int(data.get(b'stats:nombre_cas',  b'0').decode()),
                'taux':         float(data.get(b'stats:taux_incidence', b'0.0').decode()),
            })
        except Exception:
            continue

    conn.close()
    logger.info(f'{len(donnees)} enregistrements chargés depuis HBase')
    return donnees


def isolation_forest_simple(valeurs: list) -> dict:
    """
    Détection d'anomalies par méthode statistique simple
    (équivalent Isolation Forest sans sklearn).
    Seuil = moyenne + 2 * écart-type.
    """
    if len(valeurs) < 3:
        return {'seuil': max(valeurs) if valeurs else 0, 'anomalies': []}

    moyenne = np.mean(valeurs)
    ecart   = np.std(valeurs)
    seuil   = moyenne + 2 * ecart

    anomalies = [v for v in valeurs if v > seuil]
    rmse      = np.sqrt(np.mean([(v - moyenne)**2 for v in valeurs]))

    logger.info(f'Moyenne={moyenne:.2f} | Écart={ecart:.2f} | Seuil={seuil:.2f} | RMSE={rmse:.2f}')

    return {
        'moyenne':   round(moyenne, 2),
        'ecart_std': round(ecart, 2),
        'seuil':     round(seuil, 2),
        'rmse':      round(rmse, 2),
        'anomalies': anomalies,
        'nb_points': len(valeurs),
    }


def entrainer_et_sauvegarder(output_path: str):
    """Entraîne le modèle et sauvegarde les résultats."""
    os.makedirs(output_path, exist_ok=True)

    donnees   = charger_donnees_hbase()
    resultats = {}

    for maladie in ['PALUD', 'DENGUE', 'CHOLERA', 'TYPHOIDE']:
        valeurs = [d['nombre_cas'] for d in donnees if d['maladie_code'] == maladie]

        if valeurs:
            resultats[maladie] = isolation_forest_simple(valeurs)
            logger.info(f'{maladie} — RMSE : {resultats[maladie]["rmse"]}')

    # Sauvegarder les seuils en JSON
    chemin_json = os.path.join(output_path, 'seuils_model.json')
    with open(chemin_json, 'w') as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    logger.info(f'Seuils sauvegardés → {chemin_json}')

    # Générer graphique RMSE
    if resultats:
        maladies = list(resultats.keys())
        rmses    = [resultats[m]['rmse'] for m in maladies]

        plt.figure(figsize=(8, 4))
        bars = plt.bar(maladies, rmses,
                       color=['#E74C3C','#E67E22','#3498DB','#27AE60'])
        plt.title('RMSE par maladie — Sentinel-SN Équipe 02')
        plt.ylabel('RMSE')
        plt.xlabel('Maladie')
        for bar, val in zip(bars, rmses):
            plt.text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 0.1,
                     f'{val:.2f}', ha='center', fontsize=10)
        plt.tight_layout()
        chemin_png = os.path.join(output_path, 'rmse_par_maladie.png')
        plt.savefig(chemin_png, dpi=150)
        logger.info(f'Graphique RMSE → {chemin_png}')
        plt.close()

    return resultats


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-path', default='models/isolation_forest_latest')
    parser.add_argument('--window-days', type=int, default=30)
    args = parser.parse_args()

    logger.info(f'Entraînement démarré — fenêtre {args.window_days} jours')
    resultats = entrainer_et_sauvegarder(args.output_path)

    print('\n── Résultats du modèle ──')
    for maladie, stats in resultats.items():
        print(f'  {maladie:<10} | RMSE={stats["rmse"]:.2f} | Seuil={stats["seuil"]:.1f} | Anomalies={len(stats["anomalies"])}')