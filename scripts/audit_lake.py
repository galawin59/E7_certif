# -*- coding: utf-8 -*-
"""
Audit the local FICP lake folders for completeness and duplicates.
- Validates headers and row shapes
- Reports per-file stats (rows, md5)
- Detects duplicate files by identical content hash across dates
- Detects duplicate dates (multiple files with same yyyy-mm-dd name)
- Detects missing days in the continuous range for each area

Usage (from repo root):
  python scripts/audit_lake.py
Optionally pass a specific root:
  python scripts/audit_lake.py ficp_data_lake
"""
import sys
import os
import csv
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DEFAULT_LAKE = os.path.join(ROOT, 'ficp_data_lake')
DATE_FMT = '%Y-%m-%d'

EXPECTED = {
    'consultation': ['cle_bdf','date_consultation','statut_ficp','date_surveillance','date_inscription'],
    'inscription':  ['cle_bdf','statut_ficp','type_incident','date_surveillance','date_inscription'],
    'radiation':    ['cle_bdf','date_inscription','date_radiation','type_incident'],
}

class FileInfo:
    def __init__(self, path, area, date_str, rows, md5, empty):
        self.path = path
        self.area = area
        self.date_str = date_str
        self.rows = rows
        self.md5 = md5
        self.empty = empty  # True if file has header only (no data rows)


def md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        header = next(r)
        rows = list(r)
    return header, rows


def parse_date_from_filename(name: str):
    base = os.path.basename(name)
    date_part = base[:10]
    try:
        dt = datetime.strptime(date_part, DATE_FMT)
        return date_part, dt
    except Exception:
        return None, None


def audit_area(root: str, area: str):
    folder = os.path.join(root, area)
    problems = []
    infos = []

    if not os.path.isdir(folder):
        problems.append(f"Missing folder: {folder}")
        return infos, problems

    by_date = defaultdict(list)
    for name in os.listdir(folder):
        if not name.endswith('.csv'):
            continue
        date_str, dt = parse_date_from_filename(name)
        if not date_str:
            problems.append(f"Bad filename (date missing): {os.path.join(folder, name)}")
            continue
        full = os.path.join(folder, name)
        try:
            header, rows = read_csv(full)
        except Exception as ex:
            problems.append(f"Read error: {full} ({ex})")
            continue
        expected = EXPECTED[area]
        if header != expected:
            problems.append(f"Header mismatch in {full}: {header} != {expected}")
        # shape checks
        width = len(expected)
        bad_rows = 0
        for i, row in enumerate(rows, 2):
            if len(row) != width:
                bad_rows += 1
        if bad_rows:
            problems.append(f"{full}: {bad_rows} row(s) with wrong column count (expected {width})")
        # md5 & info
        digest = md5_file(full)
        infos.append(FileInfo(full, area, date_str, len(rows), digest, empty=(len(rows) == 0)))
        by_date[date_str].append(full)

    # duplicate dates
    for d, files in by_date.items():
        if len(files) > 1:
            problems.append(f"Duplicate files for date {area}/{d}: {files}")

    # continuity check
    if infos:
        dates = sorted({datetime.strptime(fi.date_str, DATE_FMT) for fi in infos})
        missing = []
        cur = dates[0]
        end = dates[-1]
        while cur <= end:
            ds = cur.strftime(DATE_FMT)
            if all(fi.date_str != ds for fi in infos):
                missing.append(ds)
            cur += timedelta(days=1)
        if missing:
            # show up to first 20 to keep output manageable
            preview = ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else "")
            problems.append(f"Missing days in {area} between {dates[0].date()} and {dates[-1].date()}: {len(missing)} missing -> {preview}")
    return infos, problems


def main(argv=None):
    argv = argv or sys.argv[1:]
    root = argv[0] if argv else DEFAULT_LAKE

    all_infos = []
    all_problems = []

    for area in ('consultation','inscription','radiation'):
        infos, problems = audit_area(root, area)
        all_infos.extend(infos)
        all_problems.extend(problems)

    # duplicates across dates by md5 (same content reused)
    by_md5 = defaultdict(list)
    for fi in all_infos:
        by_md5[fi.md5].append(fi)
    content_dups = [vals for vals in by_md5.values() if len(vals) > 1]
    # classify duplicates: all-empty vs mixed
    dup_all_empty = []
    dup_mixed = []
    for group in content_dups:
        if all(fi.empty for fi in group):
            dup_all_empty.append(group)
        else:
            dup_mixed.append(group)

    # report
    print("AUDIT SUMMARY")
    print("- files:", len(all_infos))
    total_rows = sum(fi.rows for fi in all_infos)
    print("- total rows:", total_rows)

    # per area stats
    for area in ('consultation','inscription','radiation'):
        subset = [fi for fi in all_infos if fi.area == area]
        if subset:
            dates = sorted({fi.date_str for fi in subset})
            print(f"- {area}: {len(subset)} files, range {dates[0]}..{dates[-1]}")

    # problems
    if all_problems:
        print("\nPROBLEMS:")
        for p in all_problems[:200]:
            print("-", p)
    else:
        print("\nPROBLEMS: none")

    # content duplicates across dates
    if dup_all_empty or dup_mixed:
        print("\nPOSSIBLE DUPLICATE CONTENT (same MD5 across files):")
        if dup_mixed:
            print("- Non-empty duplicates:")
            for group in dup_mixed[:50]:
                group_desc = ", ".join(f"{fi.area}/{fi.date_str}" for fi in group)
                print(f"  * {group[0].md5}: {group_desc}")
        if dup_all_empty:
            print("- Header-only (empty) duplicates:")
            for group in dup_all_empty[:50]:
                group_desc = ", ".join(f"{fi.area}/{fi.date_str}" for fi in group)
                print(f"  * {group[0].md5}: {group_desc}")
    else:
        print("\nNo identical-content duplicates detected.")

    # return non-zero if problems found
    return 1 if all_problems else 0

if __name__ == '__main__':
    raise SystemExit(main())
