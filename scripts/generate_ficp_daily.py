# -*- coding: utf-8 -*-
"""
Generation quotidienne FICP pour alimenter le data lake un jour à la fois.

Principe clé pour l'incrémentalité sans état persistant:
- Les delais (surveillance->inscription et inscription->radiation) sont déterminés par une
  fonction déterministe du cle_bdf pour garantir l'idempotence.
- Pour un jour D, on relit l'historique existant des dossiers (inscription/surveillance)
  et on calcule ce qui doit se produire à D:
  - Inscriptions PAIEMENT planifiées: pour chaque surveillance passée S, si S + delay(cle) == D
  - Radiations: pour chaque inscription passée I, si I + rad_delay(cle) == D
  - On complète avec des nouveaux événements du jour pour atteindre 300 lignes
  - On génère 1000 consultations avec 60% de clients connus

Usage:
    python scripts/generate_ficp_daily.py --date YYYY-MM-DD [--overwrite]
"""

import os
import csv
import sys
import argparse
import hashlib
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Constantes métiers
CONSULTATIONS_PAR_JOUR = 1000
EVENEMENTS_PAR_JOUR = 300
PART_SURDET = 0.30
SURV_TO_INS_DMIN, SURV_TO_INS_DMAX = 31, 37
RAD_PROBA = 0.70
RAD_DMIN, RAD_DMAX = 18, 24

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'ficp_data_lake'))
DIR_CONSULT = os.path.join(DATA_ROOT, 'consultation')
DIR_INSCR = os.path.join(DATA_ROOT, 'inscription')
DIR_RAD = os.path.join(DATA_ROOT, 'radiation')

os.makedirs(DIR_CONSULT, exist_ok=True)
os.makedirs(DIR_INSCR, exist_ok=True)
os.makedirs(DIR_RAD, exist_ok=True)

random.seed(42)


def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def md5_int(s: str) -> int:
    return int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)


def payment_delay_days(cle: str) -> int:
    # 31..37 deterministe
    return SURV_TO_INS_DMIN + (md5_int('pay:' + cle) % (SURV_TO_INS_DMAX - SURV_TO_INS_DMIN + 1))


def will_radiate(cle: str) -> bool:
    # proba deterministe ~ RAD_PROBA
    # Map hash -> [0,1) and compare
    val = (md5_int('radp:' + cle) % 10000) / 10000.0
    return val < RAD_PROBA


def radiation_delay_days(cle: str) -> int:
    # 18..24 deterministe
    return RAD_DMIN + (md5_int('radd:' + cle) % (RAD_DMAX - RAD_DMIN + 1))


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, '%Y-%m-%d')


def str_date(d: datetime) -> str:
    return d.strftime('%Y-%m-%d')


def load_history_upto(day: datetime):
    """Charge l'historique nécessaire jusqu'à (exclu) day à partir de inscription/.
    Retourne:
      - surveillances: cle -> list of surveillance dates
      - inscriptions: cle -> list of (insc_date, type_incident, surv_date_if_any)
      - known_clients: set of cle connus (depuis inscription/)
    """
    surveillances = defaultdict(list)
    inscriptions = defaultdict(list)
    known = set()

    if os.path.isdir(DIR_INSCR):
        for name in os.listdir(DIR_INSCR):
            if not name.endswith('.csv'):
                continue
            d = parse_date(name[:10])
            if d >= day:
                continue
            with open(os.path.join(DIR_INSCR, name), 'r', encoding='utf-8') as f:
                r = csv.reader(f)
                header = next(r, None)
                for cle, statut, type_inc, d_surv, d_insc in r:
                    known.add(cle)
                    if statut == 'SURVEILLANCE':
                        if d_surv:
                            surveillances[cle].append(parse_date(d_surv))
                    elif statut == 'INSCRIT':
                        insc_dt = parse_date(d_insc) if d_insc else None
                        surv_dt = parse_date(d_surv) if d_surv else None
                        if insc_dt:
                            inscriptions[cle].append((insc_dt, type_inc, surv_dt))

    # Compléter le pool de clients connus à partir de consultation/ (optionnel)
    if os.path.isdir(DIR_CONSULT):
        for name in os.listdir(DIR_CONSULT):
            if not name.endswith('.csv'):
                continue
            d = parse_date(name[:10])
            if d >= day:
                continue
            with open(os.path.join(DIR_CONSULT, name), 'r', encoding='utf-8') as f:
                r = csv.reader(f)
                header = next(r, None)
                for cle, *_ in r:
                    known.add(cle)

    return surveillances, inscriptions, known


def compute_status_for_date(cle: str, day: datetime, surveillances, inscriptions):
    # INSCRIT si une inscription existe à date <= day
    inscs = inscriptions.get(cle, [])
    if inscs:
        # prendre la plus recente <= day
        inscs_sorted = sorted([x for x in inscs if x[0] <= day], key=lambda x: x[0])
        if inscs_sorted:
            last_insc_date, type_inc, surv_dt = inscs_sorted[-1]
            return 'INSCRIT', str_date(surv_dt) if surv_dt else '', str_date(last_insc_date)

    # sinon SURVEILLANCE si une surveillance existe <= day
    survs = surveillances.get(cle, [])
    if survs:
        survs_sorted = sorted([s for s in survs if s <= day])
        if survs_sorted:
            return 'SURVEILLANCE', str_date(survs_sorted[-1]), ''

    return 'NON_INSCRIT', '', ''


def generate_daily(day: datetime, overwrite: bool = False):
    day_str = str_date(day)

    # Sortie du jour
    consult_path = os.path.join(DIR_CONSULT, f'{day_str}.csv')
    inscr_path = os.path.join(DIR_INSCR, f'{day_str}.csv')
    rad_path = os.path.join(DIR_RAD, f'{day_str}.csv')

    if not overwrite:
        for p in (consult_path, inscr_path, rad_path):
            if os.path.exists(p):
                print(f"EXISTE: {p} (utiliser --overwrite pour regénérer)")
                return 0

    # Charger l'historique jusqu'à la veille
    surveillances, inscriptions, known_clients = load_history_upto(day)

    # 1) Inscriptions PAIEMENT programmées aujourd'hui
    today_insc = []  # tuples pour inscription.csv
    paiements_today = []  # (cle, surv_dt)
    for cle, surv_list in surveillances.items():
        if not surv_list:
            continue
        # utiliser la plus recente surveillance pour ce modèle simple
        last_surv = max(surv_list)
        target = last_surv + timedelta(days=payment_delay_days(cle))
        if target == day:
            # éviter de créer doublon si déjà inscrit avant aujourd'hui
            if not any(insc_dt <= day for (insc_dt, _, _) in inscriptions.get(cle, [])):
                today_insc.append((cle, 'INSCRIT', 'PAIEMENT', str_date(last_surv), day_str))
                paiements_today.append((cle, last_surv))

    scheduled_count = len(today_insc)

    # 2) Compléter avec SURENDETTEMENT directs et nouvelles SURVEILLANCES
    remaining = max(0, EVENEMENTS_PAR_JOUR - scheduled_count)
    new_direct = int(round(remaining * PART_SURDET))
    new_surv = remaining - new_direct

    # Générer des nouvelles clés uniques
    def new_key(existing):
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        while True:
            cle = ''.join(random.choice(letters) for _ in range(8)) + ''.join(random.choice(digits) for _ in range(5))
            if cle not in existing:
                return cle

    existing_keys = set(known_clients)

    # 2.a) Direct SURENDETTEMENT
    for _ in range(new_direct):
        cle = new_key(existing_keys)
        existing_keys.add(cle)
        today_insc.append((cle, 'INSCRIT', 'SURENDETTEMENT', '', day_str))
        inscriptions[cle].append((day, 'SURENDETTEMENT', None))

    # 2.b) Nouvelles SURVEILLANCES (PAIEMENT)
    for _ in range(new_surv):
        cle = new_key(existing_keys)
        existing_keys.add(cle)
        today_insc.append((cle, 'SURVEILLANCE', 'PAIEMENT', day_str, ''))
        surveillances[cle].append(day)

    # 3) Radiations du jour (pour toutes inscriptions <= day)
    today_rad = []
    for cle, inscs in inscriptions.items():
        for (insc_dt, type_inc, _surv_dt) in inscs:
            if insc_dt >= day:
                continue
            if will_radiate(cle):
                rday = insc_dt + timedelta(days=radiation_delay_days(cle))
                if rday == day:
                    today_rad.append((cle, str_date(insc_dt), day_str, type_inc))

    # 4) Consultations 1000/jour (60% connus)
    consult_rows = []
    known_pool = list(existing_keys)
    nb_known = int(CONSULTATIONS_PAR_JOUR * 0.6)
    nb_new = CONSULTATIONS_PAR_JOUR - nb_known

    # connus
    for _ in range(nb_known):
        if known_pool:
            cle = random.choice(known_pool)
        else:
            cle = new_key(existing_keys)
            existing_keys.add(cle)
        statut, d_surv, d_insc = compute_status_for_date(cle, day, surveillances, inscriptions)
        consult_rows.append((cle, day_str, statut, d_surv, d_insc))

    # nouveaux
    for _ in range(nb_new):
        cle = new_key(existing_keys)
        existing_keys.add(cle)
        consult_rows.append((cle, day_str, 'NON_INSCRIT', '', ''))

    # 5) Écriture fichiers
    write_csv(consult_path,
              ['cle_bdf', 'date_consultation', 'statut_ficp', 'date_surveillance', 'date_inscription'],
              consult_rows)
    write_csv(inscr_path,
              ['cle_bdf', 'statut_ficp', 'type_incident', 'date_surveillance', 'date_inscription'],
              today_insc)
    write_csv(rad_path,
              ['cle_bdf', 'date_inscription', 'date_radiation', 'type_incident'],
              today_rad)

    print(f'OK - Fichiers generes pour {day_str}:')
    print(f'- {consult_path}')
    print(f'- {inscr_path}')
    print(f'- {rad_path}')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='Jour au format YYYY-MM-DD (defaut: aujourd\'hui)')
    parser.add_argument('--overwrite', action='store_true', help='Ecrase les fichiers existants du jour')
    args = parser.parse_args(argv)

    if args.date:
        try:
            day = parse_date(args.date)
        except ValueError:
            print('Date invalide, format attendu YYYY-MM-DD')
            return 2
    else:
        day = datetime.today()
        day = datetime(year=day.year, month=day.month, day=day.day)

    return generate_daily(day, overwrite=args.overwrite)


if __name__ == '__main__':
    raise SystemExit(main())
