"""Resolve unmatched station names by normalized lookup against BOM stations.txt

Usage:
    python match_unmatched_from_txt.py --bom d:/FIT3164/stations.txt --unmatched d:/FIT3164/data/unmatched.csv --out d:/FIT3164/data

Outputs:
    - unmatched_resolved.csv  (resolved via exact or fuzzy match)
    - unmatched_remaining.csv (still unmatched after attempts)
"""
from __future__ import annotations
import csv
import os
import re
import difflib
from typing import List, Dict


def normalize(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_bom_lookup(bom_path: str) -> Dict[str, Dict]:
    lookup = {}
    pattern = re.compile(r"^\s*(?P<site>\d+)\s+(?P<dist>\d+)\s+(?P<name>.{1,40}?)\s+(?P<start>\d{4}|\.{2})\s+(?P<end>\d{4}|\.{2})\s+(?P<lat>[-\d\.]+)\s+(?P<lon>[-\d\.]+)")
    with open(bom_path, 'r', encoding='utf-8', errors='replace') as f:
        started = False
        for line in f:
            if not started and re.match(r"^[-\s]+-{3,}", line):
                started = True
                continue
            if not started:
                continue
            m = pattern.match(line)
            if m:
                d = m.groupdict()
                name = d.get('name') or ''
                norm = normalize(name)
                try:
                    lat = float(d.get('lat'))
                    lon = float(d.get('lon'))
                except Exception:
                    lat = None
                    lon = None
                lookup[norm] = {'bom_name': name.strip(), 'lat': lat, 'lon': lon}
    return lookup


def read_unmatched(path: str) -> List[Dict]:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def resolve(unmatched_rows: List[Dict], bom_lookup: Dict[str, Dict], cutoff: float = 0.75):
    bom_norms = list(bom_lookup.keys())
    resolved = []
    remaining = []
    for r in unmatched_rows:
        inp = r.get('input_name') or r.get('Station') or ''
        norm = r.get('normalized') or normalize(inp)
        # exact
        if norm in bom_lookup and bom_lookup[norm]['lat'] is not None:
            rec = {'input_name': inp, 'bom_name': bom_lookup[norm]['bom_name'], 'lat': bom_lookup[norm]['lat'], 'lon': bom_lookup[norm]['lon'], 'method': 'exact'}
            resolved.append(rec)
            continue
        # fuzzy
        candidates = difflib.get_close_matches(norm, bom_norms, n=5, cutoff=cutoff)
        chosen = None
        for c in candidates:
            if bom_lookup.get(c) and bom_lookup[c]['lat'] is not None:
                chosen = bom_lookup[c]
                break
        if chosen:
            rec = {'input_name': inp, 'bom_name': chosen['bom_name'], 'lat': chosen['lat'], 'lon': chosen['lon'], 'method': 'fuzzy'}
            resolved.append(rec)
        else:
            remaining.append(r)
    return resolved, remaining


def write_results(outdir: str, resolved: List[Dict], remaining: List[Dict]):
    os.makedirs(outdir, exist_ok=True)
    res_path = os.path.join(outdir, 'unmatched_resolved.csv')
    rem_path = os.path.join(outdir, 'unmatched_remaining.csv')
    with open(res_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['input_name','bom_name','lat','lon','method'])
        writer.writeheader()
        for r in resolved:
            writer.writerow(r)
    with open(rem_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['input_name','normalized'])
        writer.writeheader()
        for r in remaining:
            writer.writerow({'input_name': r.get('input_name'), 'normalized': r.get('normalized')})
    return res_path, rem_path


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--bom', required=True)
    p.add_argument('--unmatched', required=True)
    p.add_argument('--out', default=r'd:\FIT3164\data')
    args = p.parse_args()

    bom_lookup = build_bom_lookup(args.bom)
    unmatched_rows = read_unmatched(args.unmatched)
    resolved, remaining = resolve(unmatched_rows, bom_lookup, cutoff=0.75)
    res_path, rem_path = write_results(args.out, resolved, remaining)
    print('Resolved:', len(resolved), 'Remaining:', len(remaining))
    print('Resolved written to', res_path)
    print('Remaining written to', rem_path)

if __name__ == '__main__':
    main()
