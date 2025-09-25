"""
Extract BOM stations that match a provided station list (CSV).

Usage:
  python extract_stations_by_list.py --bom d:\FIT3164\stations.txt --list d:\FIT3164\Book1.csv --out d:\FIT3164\data

Outputs:
  - matches.csv: matched rows with BOM lat/lon and the input station name
  - unmatched.csv: input station names not matched (for manual review)

Matching strategy:
  1. Parse BOM fixed-width station file (fast line-by-line regex).
  2. Normalize names (lowercase, strip punctuation, remove common tokens).
  3. Exact normalized match first, then fuzzy matching using difflib.get_close_matches.

"""
from __future__ import annotations
import argparse
import csv
import os
import re
from typing import List, Dict
import difflib


def normalize(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\(.*?\)", "", s)  # remove parenthesis
    s = re.sub(r"[^a-z0-9\s]", " ", s)  # remove punctuation
    # remove common tokens that vary
    tokens_to_strip = [r"aero", r"airport", r"raaf", r"amo", r"(defence)", r"station", r"research", r"centre", r"center", r"_", r" - "]
    for t in tokens_to_strip:
        s = re.sub(t, " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_bom_fixed(filepath: str) -> List[Dict]:
    pattern = re.compile(
        r"^\s*(?P<site>\d+)\s+(?P<dist>\d+)\s+(?P<name>.{1,40}?)\s+(?P<start>\d{4}|\.{2})\s+(?P<end>\d{4}|\.{2})\s+(?P<lat>[-\d\.]+)\s+(?P<lon>[-\d\.]+)\s+(?P<source>\S+)\s+(?P<sta>\S+)\s+(?P<height>[\d\.]+|\.{2}|\.{2,})\s+(?P<bar_ht>[\d\.]+|\.{2}|\.{2,})\s+(?P<wmo>\S+|\.{2})\s*$"
    )
    results = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        started = False
        for line in f:
            if not started and re.match(r"^[-\s]+-{3,}", line):
                started = True
                continue
            if not started:
                continue
            if not line.strip():
                continue
            m = pattern.match(line)
            if m:
                d = m.groupdict()
                name = d.get('name') or ''
                try:
                    lat = float(d.get('lat'))
                    lon = float(d.get('lon'))
                except Exception:
                    lat = None
                    lon = None
                results.append({'bom_name': name.strip(), 'lat': lat, 'lon': lon, 'site': d.get('site')})
            else:
                # fallback: split by 2+ spaces
                parts = [p for p in re.split(r"\s{2,}", line.strip()) if p]
                if parts:
                    name = parts[2] if len(parts) > 2 else parts[0]
                    lat = None
                    lon = None
                    if len(parts) > 6:
                        try:
                            lat = float(parts[5])
                            lon = float(parts[6])
                        except Exception:
                            lat = None
                            lon = None
                    results.append({'bom_name': name.strip(), 'lat': lat, 'lon': lon, 'site': None})
    return results


def read_input_list(csvpath: str) -> List[str]:
    names = []
    with open(csvpath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # try common column names
        header = reader.fieldnames
        # accept if header has 'Station' or first column
        for row in reader:
            if 'Station' in row:
                names.append(row['Station'].strip())
            else:
                # take first column
                first = list(row.values())[0]
                names.append(first.strip())
    return names


def match_lists(input_names: List[str], bom_records: List[Dict], cutoff: float = 0.85):
    # Build normalized lookup for BOM
    bom_map = {}
    bom_norms = []
    for r in bom_records:
        norm = normalize(r['bom_name'])
        bom_map[norm] = r
        bom_norms.append(norm)

    matches = []
    unmatched = []

    for name in input_names:
        n = normalize(name)
        if n in bom_map and bom_map[n]['lat'] is not None:
            rec = bom_map[n].copy()
            rec['input_name'] = name
            rec['match_type'] = 'exact'
            matches.append(rec)
            continue
        # fuzzy match
        candidates = difflib.get_close_matches(n, bom_norms, n=3, cutoff=cutoff)
        if candidates:
            # pick first candidate with lat/lon
            chosen = None
            for c in candidates:
                if bom_map.get(c) and bom_map[c]['lat'] is not None:
                    chosen = bom_map[c]
                    break
            if chosen:
                rec = chosen.copy()
                rec['input_name'] = name
                rec['match_type'] = 'fuzzy'
                rec['match_score'] = difflib.SequenceMatcher(None, n, normalize(chosen['bom_name'])).ratio()
                matches.append(rec)
                continue
        # not matched
        unmatched.append({'input_name': name, 'normalized': n})
    return matches, unmatched


def write_csv(outdir: str, matches: List[Dict], unmatched: List[Dict]):
    os.makedirs(outdir, exist_ok=True)
    matches_path = os.path.join(outdir, 'matches.csv')
    unmatched_path = os.path.join(outdir, 'unmatched.csv')
    with open(matches_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['input_name', 'bom_name', 'site', 'lat', 'lon', 'match_type', 'match_score'])
        writer.writeheader()
        for m in matches:
            writer.writerow({
                'input_name': m.get('input_name'),
                'bom_name': m.get('bom_name'),
                'site': m.get('site'),
                'lat': m.get('lat'),
                'lon': m.get('lon'),
                'match_type': m.get('match_type'),
                'match_score': m.get('match_score', '')
            })
    with open(unmatched_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['input_name', 'normalized'])
        writer.writeheader()
        for u in unmatched:
            writer.writerow(u)
    return matches_path, unmatched_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bom', required=True, help='Path to BOM stations.txt')
    p.add_argument('--list', required=True, help='CSV file with Station names (Book1.csv)')
    p.add_argument('--out', default=r'd:\FIT3164\data', help='Output directory')
    p.add_argument('--cutoff', type=float, default=0.85, help='Fuzzy match cutoff (0-1)')
    args = p.parse_args()

    bom_records = parse_bom_fixed(args.bom)
    input_names = read_input_list(args.list)
    matches, unmatched = match_lists(input_names, bom_records, cutoff=args.cutoff)
    matches_path, unmatched_path = write_csv(args.out, matches, unmatched)
    print(f'Matches: {len(matches)}, Unmatched: {len(unmatched)}')
    print('Matches written to', matches_path)
    print('Unmatched written to', unmatched_path)


if __name__ == '__main__':
    import argparse
    main()
