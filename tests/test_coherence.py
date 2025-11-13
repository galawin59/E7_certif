# -*- coding: utf-8 -*-
import os
import csv
from datetime import datetime, timedelta

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


def test_structure_exists():
    assert os.path.isdir(C_DIR)
    assert os.path.isdir(I_DIR)
    assert os.path.isdir(R_DIR)


def load_all_inscriptions():
    surv = {}  # cle -> list of surv dates
    insc = {}  # cle -> list of (date, type)
    for name in os.listdir(I_DIR):
        if not name.endswith('.csv'):
            continue
        d = datetime.strptime(name[:10], DATE_FMT)
        header, rows = read_csv(os.path.join(I_DIR, name))
        for cle, statut, type_inc, d_surv, d_insc in rows:
            if statut == 'SURVEILLANCE':
                surv.setdefault(cle, []).append(datetime.strptime(d_surv, DATE_FMT))
            elif statut == 'INSCRIT':
                insc.setdefault(cle, []).append((datetime.strptime(d_insc, DATE_FMT), type_inc))
    return surv, insc


def test_business_rules_core():
    surv, insc = load_all_inscriptions()

    # 1) Chaque inscription PAIEMENT doit avoir une surveillance 31..37 jours avant
    for cle, entries in insc.items():
        for d_insc, type_inc in entries:
            if type_inc == 'PAIEMENT':
                assert cle in surv, f"Inscription PAIEMENT sans surveillance pour {cle}"
                ok = False
                for d_surv in surv.get(cle, []):
                    delta = (d_insc - d_surv).days
                    if 31 <= delta <= 37:
                        ok = True
                        break
                assert ok, f"Delai PAIEMENT invalide pour {cle}: {entries} vs {surv.get(cle)}"

    # 2) Aucune surveillance avec type_incident = SURENDETTEMENT dans les fichiers
    for name in os.listdir(I_DIR):
        if not name.endswith('.csv'):
            continue
        header, rows = read_csv(os.path.join(I_DIR, name))
        for _, statut, type_inc, _, _ in rows:
            if statut == 'SURVEILLANCE':
                assert type_inc == 'PAIEMENT'

    # 3) Radiations uniquement après inscription
    for name in os.listdir(R_DIR):
        if not name.endswith('.csv'):
            continue
        d = datetime.strptime(name[:10], DATE_FMT)
        header, rows = read_csv(os.path.join(R_DIR, name))
        for cle, d_insc, d_rad, type_inc in rows:
            di = datetime.strptime(d_insc, DATE_FMT)
            dr = datetime.strptime(d_rad, DATE_FMT)
            assert dr > di
            # vérifier qu'une inscription existe pour ce cle
            assert cle in insc, f"Radiation sans inscription pour {cle}"
            assert any(di == x[0] for x in insc[cle]), f"Radiation ne correspond pas a l'inscription pour {cle}"


def test_consultation_chronology():
    # Les dates de surveillance doivent preceder la date_inscription quand presentes
    # Et statut coherent avec dates
    for name in os.listdir(C_DIR):
        if not name.endswith('.csv'):
            continue
        d = datetime.strptime(name[:10], DATE_FMT)
        header, rows = read_csv(os.path.join(C_DIR, name))
        for cle, d_cons, statut, d_surv, d_insc in rows:
            if d_surv:
                assert datetime.strptime(d_surv, DATE_FMT) <= datetime.strptime(d_cons, DATE_FMT)
            if d_insc:
                assert datetime.strptime(d_insc, DATE_FMT) <= datetime.strptime(d_cons, DATE_FMT)
            if statut == 'SURVEILLANCE':
                assert d_surv and not d_insc
            if statut == 'INSCRIT':
                assert d_insc
