from functools import lru_cache
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .config import DATA_DIR, GRID_PATH, MAP_PATH, MODIS_PATH, MODEL_PATH, REGIONS

@lru_cache(maxsize=1)
def grid():
    if not GRID_PATH.exists():
        raise FileNotFoundError(f'Missing processed dataset: {GRID_PATH}')
    df = pd.read_csv(GRID_PATH, compression='gzip')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df.dropna(subset=['date'])

@lru_cache(maxsize=1)
def map_points():
    if not MAP_PATH.exists():
        return pd.DataFrame(columns=['latitude','longitude','frp','brightness','confidence','acq_date','acq_time','satellite','instrument','daynight','type'])
    return pd.read_csv(MAP_PATH, compression='gzip')

@lru_cache(maxsize=1)
def modis_grid():
    if not MODIS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(MODIS_PATH, compression='gzip')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['is_anomaly'] = False
    df['anomaly_score'] = 0.0
    if 'brightness_mean' not in df: df['brightness_mean'] = 0.0
    if 'confidence_mean' not in df: df['confidence_mean'] = 0.0
    if 'night_count' not in df: df['night_count'] = 0
    return df.dropna(subset=['date'])

@lru_cache(maxsize=1)
def modis_map_points():
    path = DATA_DIR / 'modis_map_sample.csv.gz'
    return pd.read_csv(path, compression='gzip') if path.exists() else pd.DataFrame()

@lru_cache(maxsize=1)
def metadata():
    path = DATA_DIR / 'training_metadata.json'
    return json.loads(path.read_text()) if path.exists() else {}

@lru_cache(maxsize=1)
def anomaly_model():
    import joblib
    return joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None

def bounds_for(region_id='global', south=None, north=None, west=None, east=None):
    region = next((r for r in REGIONS if r['id'] == region_id), REGIONS[0])
    b = region['bounds']
    return (float(south if south is not None else b[0]), float(north if north is not None else b[1]),
            float(west if west is not None else b[2]), float(east if east is not None else b[3]))

def filter_grid(region_id='global', south=None, north=None, west=None, east=None, start_date=None, end_date=None, mode='viirs'):
    s, n, w, e = bounds_for(region_id, south, north, west, east)
    df = modis_grid() if mode == 'modis' else grid()
    if mode == 'modis' and df.empty:
        return df, (s, n, w, e)
    # Cells are represented by their lower-left 5-degree coordinate.
    mask = (df.lat_cell >= np.floor(s / 5) * 5) & (df.lat_cell <= np.floor(n / 5) * 5) & (df.lon_cell >= np.floor(w / 5) * 5) & (df.lon_cell <= np.floor(e / 5) * 5)
    out = df.loc[mask]
    if start_date:
        out = out[out.date >= pd.to_datetime(start_date)]
    if end_date:
        out = out[out.date <= pd.to_datetime(end_date)]
    if mode == 'harmonized' and not out.empty:
        cal_path = DATA_DIR / 'modis_calibration.json'
        if cal_path.exists():
            calibration = json.loads(cal_path.read_text())
            out = out.copy()
            out['hotspot_count'] = np.maximum(0, np.expm1(calibration['countIntercept'] + calibration['countSlope'] * np.log1p(out['hotspot_count'])))
    return out, (s, n, w, e)

def region_map(region_id='global', south=None, north=None, west=None, east=None, start_date=None, end_date=None, limit=2500, mode='viirs'):
    s, n, w, e = bounds_for(region_id, south, north, west, east)
    df = modis_map_points() if mode == 'modis' else map_points()
    if mode == 'modis' and df.empty:
        return df
    mask = df.latitude.between(s, n) & df.longitude.between(w, e)
    if start_date: mask &= df.acq_date >= str(start_date)
    if end_date: mask &= df.acq_date <= str(end_date)
    out = df.loc[mask]
    if len(out) > limit:
        # Deterministic even sampling avoids repeatedly showing the same dense leading rows.
        out = out.iloc[np.linspace(0, len(out)-1, limit, dtype=int)]
    return out

def _monthly(daily):
    """Return chronological calendar months (year is retained across multi-year AOIs)."""
    if daily.empty: return []
    d = daily.copy()
    d['month_start'] = d.date.dt.to_period('M').dt.to_timestamp()
    rows=[]
    for month_start, g in d.groupby('month_start', sort=True):
        vals = g.hotspot_count.astype(float)
        rows.append({'month': month_start.strftime("%b '%y"),
                     'monthNumber': int(month_start.strftime('%Y%m')),
                     'hotspotCount': int(vals.sum()),
                     'meanDaily': round(float(vals.mean()), 1),
                     'threshold90': round(float(vals.quantile(.9)), 1),
                     'anomalyDays': int(g.get('is_anomaly', pd.Series(False,index=g.index)).sum()),
                     'frpMean': round(float(g.frp_sum.sum()), 1)})
    return rows

def get_calendar(df):
    if df.empty: return []
    daily = df.groupby('date', as_index=False).agg(hotspot_count=('hotspot_count','sum'), frp_sum=('frp_sum','sum'), is_anomaly=('is_anomaly','max'))
    return _monthly(daily)

def summary(region_id='global', mode='viirs', **kwargs):
    df, bounds = filter_grid(region_id, mode=mode, **kwargs)
    if df.empty:
        return {'hotspotCount':0,'frpTotal':0,'activeCells':0,'anomalyCells':0,'latestDate':None,'anomalyRate':0,'bounds':bounds}
    daily = df.groupby('date',as_index=False).agg(hotspot_count=('hotspot_count','sum'),frp_sum=('frp_sum','sum'))
    latest = df.date.max()
    latest_cells = df[df.date == latest]
    return {'hotspotCount':int(df.hotspot_count.sum()),'frpTotal':round(float(df.frp_sum.sum()),1),
            'activeCells':int(df[['lat_cell','lon_cell']].drop_duplicates().shape[0]),
            'anomalyCells':int(df.is_anomaly.sum()),'latestDate':latest.strftime('%Y-%m-%d'),
            'anomalyRate':round(float(df.is_anomaly.mean()*100),1),'latestDayCount':int(daily.loc[daily.date==latest,'hotspot_count'].sum()),
            'latestDayAnomaly':bool(latest_cells.is_anomaly.any()),'bounds':bounds}

def alerts(region_id='global', **kwargs):
    df, _ = filter_grid(region_id, **kwargs)
    if df.empty: return []
    a = df[df.anomaly_score >= 80].sort_values(['date','anomaly_score'],ascending=[False,False]).head(30)
    return [{'date':r.date.strftime('%Y-%m-%d'),'latitude':float(r.lat_cell+2.5),'longitude':float(r.lon_cell+2.5),
             'hotspotCount':int(r.hotspot_count),'frp':round(float(r.frp_sum),1),'score':float(r.anomaly_score),
             'severity':'HIGH' if r.anomaly_score>=90 else 'ELEVATED'} for r in a.itertuples()]

def analytics(region_id='global', **kwargs):
    df, _ = filter_grid(region_id, mode='viirs', **kwargs)
    viirs_count = int(df.hotspot_count.sum()) if not df.empty else 0
    viirs_frp = float(df.frp_sum.sum()) if not df.empty else 0
    result={'viirs':{'count':viirs_count,'frp':round(viirs_frp,1)},'modis':None,'calibration':None,'comparisonAvailable':False}
    if MODIS_PATH.exists():
        mod = pd.read_csv(MODIS_PATH, compression='gzip')
        mod['date']=pd.to_datetime(mod.date,errors='coerce')
        s,n,w,e=bounds_for(region_id,kwargs.get('south'),kwargs.get('north'),kwargs.get('west'),kwargs.get('east'))
        mod=mod[(mod.lat_cell>=np.floor(s/5)*5)&(mod.lat_cell<=np.floor(n/5)*5)&(mod.lon_cell>=np.floor(w/5)*5)&(mod.lon_cell<=np.floor(e/5)*5)]
        if kwargs.get('start_date'): mod=mod[mod.date>=pd.to_datetime(kwargs['start_date'])]
        if kwargs.get('end_date'): mod=mod[mod.date<=pd.to_datetime(kwargs['end_date'])]
        result['modis']={'count':int(mod.hotspot_count.sum()),'frp':round(float(mod.frp_sum.sum()),1)}
        cal_path=DATA_DIR/'modis_calibration.json'
        if cal_path.exists(): result['calibration']=json.loads(cal_path.read_text())
        result['comparisonAvailable']=True
    return result
