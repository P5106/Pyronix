"""Download official NASA FIRMS active-fire CSV data for a bounded AOI.

Requires a free FIRMS MAP_KEY. The FIRMS Area API returns at most five days per
request. This script downloads date windows and combines them into one CSV.
"""
import argparse
from datetime import date, timedelta
from pathlib import Path
import time
import os
import requests
import pandas as pd

BASE = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv'
SOURCES = {'MODIS': 'MODIS_SP', 'VIIRS_SNPP': 'VIIRS_SNPP_SP',
           'VIIRS_NOAA20': 'VIIRS_NOAA20_SP', 'VIIRS_NOAA21': 'VIIRS_NOAA21_SP'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--map-key', default=os.getenv('NASA_FIRMS_MAP_KEY'), help='NASA FIRMS MAP_KEY; alternatively set NASA_FIRMS_MAP_KEY in your environment')
    p.add_argument('--sensor', choices=SOURCES, required=True)
    p.add_argument('--area', default='world', help='world or west,south,east,north')
    p.add_argument('--start', required=True, help='YYYY-MM-DD')
    p.add_argument('--end', required=True, help='YYYY-MM-DD')
    p.add_argument('--output', required=True, help='Output CSV path')
    args = p.parse_args()
    if not args.map_key:
        p.error('Provide --map-key or set the NASA_FIRMS_MAP_KEY environment variable.')
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start:
        p.error('--end must be on or after --start')
    source = SOURCES[args.sensor]
    chunks, cursor = [], start
    while cursor <= end:
        days = min(5, (end - cursor).days + 1)
        url = f'{BASE}/{args.map_key}/{source}/{args.area}/{days}/{cursor.isoformat()}'
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        if not response.text.strip() or response.text.lstrip().startswith('Invalid'):
            raise RuntimeError(f'FIRMS returned an invalid response for {cursor}: {response.text[:300]}')
        from io import StringIO
        frame = pd.read_csv(StringIO(response.text))
        if not {'latitude', 'longitude', 'acq_date', 'frp'}.issubset(frame.columns):
            raise RuntimeError(f'Unexpected FIRMS CSV schema: {frame.columns.tolist()}')
        chunks.append(frame)
        print(f'{cursor}..{cursor + timedelta(days=days-1)}: {len(frame):,} detections')
        cursor += timedelta(days=days)
        time.sleep(0.25)
    result = pd.concat(chunks, ignore_index=True).drop_duplicates()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    print(f'Saved {len(result):,} {args.sensor} detections to {out.resolve()}')

if __name__ == '__main__':
    main()
