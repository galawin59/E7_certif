# Azure Function: Daily FICP generator (Timer Trigger)
import datetime
import csv
import io
import os
import hashlib
from datetime import datetime as dt, timedelta
from collections import defaultdict

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


# Deterministic helpers
def md5_int(s: str) -> int:
    return int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)


SURV_TO_INS_DMIN, SURV_TO_INS_DMAX = 31, 37
RAD_PROBA = 0.70
RAD_DMIN, RAD_DMAX = 18, 24
CONSULTATIONS_PAR_JOUR = 1000
EVENEMENTS_PAR_JOUR = 300
PART_SURDET = 0.30


def payment_delay_days(cle: str) -> int:
    return SURV_TO_INS_DMIN + (md5_int('pay:' + cle) % (SURV_TO_INS_DMAX - SURV_TO_INS_DMIN + 1))


def will_radiate(cle: str) -> bool:
    val = (md5_int('radp:' + cle) % 10000) / 10000.0
    return val < RAD_PROBA


def radiation_delay_days(cle: str) -> int:
    return RAD_DMIN + (md5_int('radd:' + cle) % (RAD_DMAX - RAD_DMIN + 1))


def str_date(d: dt) -> str:
    return d.strftime('%Y-%m-%d')


def parse_date(s: str) -> dt:
    return dt.strptime(s, '%Y-%m-%d')


def list_blobs(client, container: str, prefix: str):
    return client.get_container_client(container).list_blobs(name_starts_with=prefix)


def download_text(client, container: str, name: str) -> str:
    blob = client.get_blob_client(container=container, blob=name)
    return blob.download_blob().content_as_text(encoding='utf-8')


def upload_csv(client, container: str, name: str, header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(header)
    w.writerows(rows)
    data = buf.getvalue().encode('utf-8')
    blob = client.get_blob_client(container=container, blob=name)
    blob.upload_blob(data, overwrite=True, content_type='text/csv')


def load_history_upto(client, container: str, day: dt):
    surveillances = defaultdict(list)
    inscriptions = defaultdict(list)
    known = set()

    # inscriptions/
    for b in list_blobs(client, container, 'inscription/'):
        try:
            d = parse_date(os.path.basename(b.name)[:10])
        except Exception:
            continue
        if d >= day:
            continue
        text = download_text(client, container, b.name)
        r = csv.reader(io.StringIO(text))
        header = next(r, None)
        for cle, statut, type_inc, d_surv, d_insc in r:
            known.add(cle)
            if statut == 'SURVEILLANCE' and d_surv:
                surveillances[cle].append(parse_date(d_surv))
            elif statut == 'INSCRIT' and d_insc:
                inscriptions[cle].append((parse_date(d_insc), type_inc, parse_date(d_surv) if d_surv else None))

    # consultation/ (optionnel pour enrichir known)
    for b in list_blobs(client, container, 'consultation/'):
        try:
            d = parse_date(os.path.basename(b.name)[:10])
        except Exception:
            continue
        if d >= day:
            continue
        text = download_text(client, container, b.name)
        r = csv.reader(io.StringIO(text))
        header = next(r, None)
        for cle, *_ in r:
            known.add(cle)

    return surveillances, inscriptions, known


def compute_status_for_date(cle: str, day: dt, surveillances, inscriptions):
    inscs = inscriptions.get(cle, [])
    if inscs:
        inscs_sorted = sorted([x for x in inscs if x[0] <= day], key=lambda x: x[0])
        if inscs_sorted:
            last_insc_date, type_inc, surv_dt = inscs_sorted[-1]
            return 'INSCRIT', str_date(surv_dt) if surv_dt else '', str_date(last_insc_date)
    survs = surveillances.get(cle, [])
    if survs:
        survs_sorted = sorted([s for s in survs if s <= day])
        if survs_sorted:
            return 'SURVEILLANCE', str_date(survs_sorted[-1]), ''
    return 'NON_INSCRIT', '', ''


def new_key(existing):
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    import random
    while True:
        cle = ''.join(random.choice(letters) for _ in range(8)) + ''.join(random.choice(digits) for _ in range(5))
        if cle not in existing:
            return cle


def main_logic(day: dt, client: BlobServiceClient, container: str):
    day_str = str_date(day)
    surveillances, inscriptions, known_clients = load_history_upto(client, container, day)

    today_insc = []
    # inscriptions PAIEMENT planifiées aujourd'hui
    for cle, surv_list in surveillances.items():
        if not surv_list:
            continue
        last_surv = max(surv_list)
        if last_surv + timedelta(days=payment_delay_days(cle)) == day:
            # eviter doublon si inscription deja enregistree <= day
            if not any(insc_dt <= day for (insc_dt, _t, _s) in inscriptions.get(cle, [])):
                today_insc.append((cle, 'INSCRIT', 'PAIEMENT', str_date(last_surv), day_str))

    scheduled_count = len(today_insc)
    remaining = max(0, EVENEMENTS_PAR_JOUR - scheduled_count)
    new_direct = int(round(remaining * PART_SURDET))
    new_surv = remaining - new_direct

    existing = set(known_clients)
    # Direct SURENDETTEMENT
    for _ in range(new_direct):
        cle = new_key(existing)
        existing.add(cle)
        today_insc.append((cle, 'INSCRIT', 'SURENDETTEMENT', '', day_str))
        inscriptions[cle].append((day, 'SURENDETTEMENT', None))

    # Nouvelles SURVEILLANCES
    for _ in range(new_surv):
        cle = new_key(existing)
        existing.add(cle)
        today_insc.append((cle, 'SURVEILLANCE', 'PAIEMENT', day_str, ''))
        surveillances[cle].append(day)

    # Radiations du jour
    today_rad = []
    for cle, inscs in inscriptions.items():
        for (insc_dt, type_inc, _surv_dt) in inscs:
            if insc_dt >= day:
                continue
            if will_radiate(cle):
                rday = insc_dt + timedelta(days=radiation_delay_days(cle))
                if rday == day:
                    today_rad.append((cle, str_date(insc_dt), day_str, type_inc))

    # Consultations
    consult_rows = []
    import random
    known_pool = list(existing)
    nb_known = int(CONSULTATIONS_PAR_JOUR * 0.6)
    nb_new = CONSULTATIONS_PAR_JOUR - nb_known
    for _ in range(nb_known):
        cle = random.choice(known_pool) if known_pool else new_key(existing)
        statut, d_surv, d_insc = compute_status_for_date(cle, day, surveillances, inscriptions)
        consult_rows.append((cle, day_str, statut, d_surv, d_insc))
    for _ in range(nb_new):
        cle = new_key(existing)
        existing.add(cle)
        consult_rows.append((cle, day_str, 'NON_INSCRIT', '', ''))

    # Upload files
    upload_csv(client, container, f'consultation/{day_str}.csv',
               ['cle_bdf', 'date_consultation', 'statut_ficp', 'date_surveillance', 'date_inscription'],
               consult_rows)
    upload_csv(client, container, f'inscription/{day_str}.csv',
               ['cle_bdf', 'statut_ficp', 'type_incident', 'date_surveillance', 'date_inscription'],
               today_insc)
    upload_csv(client, container, f'radiation/{day_str}.csv',
               ['cle_bdf', 'date_inscription', 'date_radiation', 'type_incident'],
               today_rad)


def main(mytimer: func.TimerRequest) -> None:
    # Determine day from schedule run; default to today in local time (WEBSITE_TIME_ZONE can be set)
    now = dt.now()
    day = dt(year=now.year, month=now.month, day=now.day)

    account = os.environ.get('TARGET_STORAGE_ACCOUNT')
    container = os.environ.get('TARGET_CONTAINER', 'ficp')
    if not account:
        raise RuntimeError('Missing TARGET_STORAGE_ACCOUNT app setting')

    # Use managed identity
    url = f'https://{account}.blob.core.windows.net'
    credential = DefaultAzureCredential()
    client = BlobServiceClient(account_url=url, credential=credential)

    main_logic(day, client, container)
