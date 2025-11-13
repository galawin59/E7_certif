# -*- coding: utf-8 -*-
import os
import csv
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DL = os.path.join(ROOT, 'ficp_data_lake')
C_DIR = os.path.join(DL, 'consultation')
I_DIR = os.path.join(DL, 'inscription')
R_DIR = os.path.join(DL, 'radiation')

DATE_FMT = '%Y-%m-%d'

def read_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        header = next(r)
        return header, list(r)

def main():
    errors = []

    # Structure
    if not os.path.isdir(C_DIR): errors.append('consultation/ manquant')
    if not os.path.isdir(I_DIR): errors.append('inscription/ manquant')
    if not os.path.isdir(R_DIR): errors.append('radiation/ manquant')

    # Charger inscriptions
    surv = {}
    insc = {}
    for name in os.listdir(I_DIR):
        if not name.endswith('.csv'): continue
        header, rows = read_csv(os.path.join(I_DIR, name))
        for cle, statut, type_inc, d_surv, d_insc in rows:
            if statut == 'SURVEILLANCE':
                if type_inc != 'PAIEMENT':
                    errors.append(f'SURVEILLANCE non PAIEMENT pour {cle}')
                if d_surv:
                    surv.setdefault(cle, []).append(datetime.strptime(d_surv, DATE_FMT))
            elif statut == 'INSCRIT':
                if d_insc:
                    insc.setdefault(cle, []).append((datetime.strptime(d_insc, DATE_FMT), type_inc))

    # Regles PAIEMENT: delai 31..37
    for cle, entries in insc.items():
        for d_insc, type_inc in entries:
            if type_inc == 'PAIEMENT':
                if cle not in surv:
                    errors.append(f'Inscription PAIEMENT sans surveillance pour {cle}')
                    continue
                if not any(31 <= (d_insc - ds).days <= 37 for ds in surv[cle]):
                    errors.append(f'Delai PAIEMENT invalide pour {cle}')

    # Radiations: apres inscription
    for name in os.listdir(R_DIR):
        if not name.endswith('.csv'): continue
        header, rows = read_csv(os.path.join(R_DIR, name))
        for cle, d_insc, d_rad, type_inc in rows:
            di = datetime.strptime(d_insc, DATE_FMT)
            dr = datetime.strptime(d_rad, DATE_FMT)
            if dr <= di:
                errors.append(f'Radiation avant inscription pour {cle}')
            if cle not in insc or not any(di == x[0] for x in insc[cle]):
                errors.append(f'Radiation sans inscription correspondante pour {cle}')

    if errors:
        print('VALIDATION: FAIL')
        for e in errors[:50]:
            print('-', e)
        return 1
    else:
        print('VALIDATION: PASS')
        return 0

if __name__ == '__main__':
    raise SystemExit(main())