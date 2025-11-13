# -*- coding: utf-8 -*-
"""
Generateur FICP - Data Lake simule (E7 Bloc 4)
- Period: 2025-01-01 -> 2025-11-13
- Volumes: 1000 consultations/jour, 300 evenements (surveillance+inscription)/jour
- 70% des inscrits radies ~20 jours apres l'inscription
- Regles metier FICP respectees
"""

import os
import csv
import random
from datetime import datetime, timedelta
from collections import defaultdict, deque

# Constantes
DATE_DEBUT = datetime(2025, 1, 1)
DATE_FIN = datetime(2025, 11, 13)
CONSULTATIONS_PAR_JOUR = 1000
EVENEMENTS_PAR_JOUR = 300  # total lignes/jour dans inscription.csv (SURVEILLANCE + INSCRIT)
PART_SURDET = 0.30  # part des inscriptions directes SURENDETTEMENT parmi les nouveaux evenements
RADIATION_PROBA = 0.70
RADIATION_J_MIN, RADIATION_J_MAX = 18, 24  # autour de 20 jours
SURV_TO_INS_MIN, SURV_TO_INS_MAX = 31, 37

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'ficp_data_lake'))
DIR_CONSULT = os.path.join(DATA_ROOT, 'consultation')
DIR_INSCR = os.path.join(DATA_ROOT, 'inscription')
DIR_RAD = os.path.join(DATA_ROOT, 'radiation')

os.makedirs(DIR_CONSULT, exist_ok=True)
os.makedirs(DIR_INSCR, exist_ok=True)
os.makedirs(DIR_RAD, exist_ok=True)

random.seed(42)

# Etat des clients
# state[cle] = {
#   'surv_date': date or None,
#   'insc_date': date or None,
#   'type_incident': 'PAIEMENT'|'SURENDETTEMENT'|None
# }
state = {}

# Schedulers par date
scheduled_inscriptions = defaultdict(list)  # date -> [(cle, surv_date, 'PAIEMENT')]
scheduled_radiations = defaultdict(list)    # date -> [(cle, insc_date, type_incident)]

# Générateur de cle_bdf pseudonymisée (13 chars)
def gen_cle_bdf():
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    return ''.join(random.choice(letters) for _ in range(8)) + ''.join(random.choice(digits) for _ in range(5))

# Utilitaire d'écriture CSV

def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

# Déterminer statut FICP pour consultation à une date donnee

def compute_statut_for_date(cle, d):
    info = state.get(cle)
    if not info:
        return 'NON_INSCRIT', '', ''
    insc = info.get('insc_date')
    surv = info.get('surv_date')
    if insc and insc <= d:
        return 'INSCRIT', (surv.strftime('%Y-%m-%d') if surv else ''), insc.strftime('%Y-%m-%d')
    if surv and surv <= d:
        return 'SURVEILLANCE', surv.strftime('%Y-%m-%d'), ''
    return 'NON_INSCRIT', '', ''

# Boucle principale par jour

def main():
    day = DATE_DEBUT
    all_known_clients = set()

    while day <= DATE_FIN:
        day_str = day.strftime('%Y-%m-%d')

        # 1) Appliquer les inscriptions programmées (PAIEMENT)
        todays_inscriptions = []
        for cle, surv_date, type_inc in scheduled_inscriptions.get(day, []):
            # inscription effective aujourd'hui
            state.setdefault(cle, {})['insc_date'] = day
            state[cle]['type_incident'] = type_inc  # 'PAIEMENT'
            todays_inscriptions.append((cle, 'INSCRIT', type_inc, surv_date.strftime('%Y-%m-%d'), day_str))
            # programmer radiation
            if random.random() < RADIATION_PROBA:
                rad_day = day + timedelta(days=random.randint(RADIATION_J_MIN, RADIATION_J_MAX))
                if rad_day <= DATE_FIN:
                    scheduled_radiations[rad_day].append((cle, day, type_inc))

        # 2) Appliquer les radiations programmées
        todays_radiations = []
        for cle, insc_date, type_inc in scheduled_radiations.get(day, []):
            todays_radiations.append((cle, insc_date.strftime('%Y-%m-%d'), day_str, type_inc))
            # la radiation ne change pas l'état d'inscription (client reste historisé comme inscrit puis radié)

        # 3) Créer de nouveaux événements pour atteindre EXACTEMENT 300 lignes totales aujourd'hui dans inscription.csv
        remaining = max(0, EVENEMENTS_PAR_JOUR - len(todays_inscriptions))
        # nouveaux evenements = direct surendettement (INSCRIT) + surveillances (PAIEMENT)
        new_direct = int(round(remaining * PART_SURDET))
        new_surv = remaining - new_direct

        new_inscriptions_rows = []

        # 3.a) Direct SURENDETTEMENT -> INSCRIT aujourd'hui
        for _ in range(new_direct):
            cle = gen_cle_bdf()
            while cle in all_known_clients:
                cle = gen_cle_bdf()
            all_known_clients.add(cle)
            state[cle] = {
                'surv_date': None,
                'insc_date': day,
                'type_incident': 'SURENDETTEMENT'
            }
            new_inscriptions_rows.append((cle, 'INSCRIT', 'SURENDETTEMENT', '', day_str))
            # Radiation potentielle
            if random.random() < RADIATION_PROBA:
                rad_day = day + timedelta(days=random.randint(RADIATION_J_MIN, RADIATION_J_MAX))
                if rad_day <= DATE_FIN:
                    scheduled_radiations[rad_day].append((cle, day, 'SURENDETTEMENT'))

        # 3.b) Surveillances (PAIEMENT) -> inscription programmée [31,37] jours
        for _ in range(new_surv):
            cle = gen_cle_bdf()
            while cle in all_known_clients:
                cle = gen_cle_bdf()
            all_known_clients.add(cle)
            surv_date = day
            state[cle] = {
                'surv_date': surv_date,
                'insc_date': None,
                'type_incident': None
            }
            new_inscriptions_rows.append((cle, 'SURVEILLANCE', 'PAIEMENT', surv_date.strftime('%Y-%m-%d'), ''))
            # programmer inscription (PAIEMENT)
            future = day + timedelta(days=random.randint(SURV_TO_INS_MIN, SURV_TO_INS_MAX))
            if future <= DATE_FIN:
                scheduled_inscriptions[future].append((cle, surv_date, 'PAIEMENT'))

        # Fusionner tous les evenements d'inscription du jour
        inscription_rows = todays_inscriptions + new_inscriptions_rows

        # 4) Générer consultations (1000/jour)
        consultation_rows = []
        # stratégie : 60% clients connus, 40% nouveaux
        known_pool = list(all_known_clients)
        nb_known = int(CONSULTATIONS_PAR_JOUR * 0.6)
        nb_new = CONSULTATIONS_PAR_JOUR - nb_known

        # clients connus
        for _ in range(nb_known):
            if known_pool:
                cle = random.choice(known_pool)
            else:
                cle = gen_cle_bdf()
                all_known_clients.add(cle)
            statut, d_surv, d_insc = compute_statut_for_date(cle, day)
            consultation_rows.append((cle, day_str, statut, d_surv, d_insc))

        # nouveaux clients (non inscrits par défaut)
        for _ in range(nb_new):
            cle = gen_cle_bdf()
            while cle in all_known_clients:
                cle = gen_cle_bdf()
            all_known_clients.add(cle)
            consultation_rows.append((cle, day_str, 'NON_INSCRIT', '', ''))

        # 5) Ecriture des fichiers du jour
        consult_path = os.path.join(DIR_CONSULT, f'{day_str}.csv')
        inscr_path = os.path.join(DIR_INSCR, f'{day_str}.csv')
        rad_path = os.path.join(DIR_RAD, f'{day_str}.csv')

        write_csv(consult_path, ['cle_bdf', 'date_consultation', 'statut_ficp', 'date_surveillance', 'date_inscription'], consultation_rows)
        write_csv(inscr_path, ['cle_bdf', 'statut_ficp', 'type_incident', 'date_surveillance', 'date_inscription'], inscription_rows)
        write_csv(rad_path, ['cle_bdf', 'date_inscription', 'date_radiation', 'type_incident'], todays_radiations)

        day += timedelta(days=1)

    print('Generation terminee:')
    print(f'- Dossiers: {DATA_ROOT}')

if __name__ == '__main__':
    main()
