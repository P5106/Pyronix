from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd, numpy as np, json
from sklearn.linear_model import HuberRegressor
from .config import REGIONS, DATA_DIR, MODIS_PATH
from . import data_service as ds

app=FastAPI(title='Pyronix Fire Harmonization API',version='1.0.0',description='VIIRS fire activity analytics and optional MODIS cross-calibration.')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

@app.get('/api/health')
def health():
    return {'status':'ok','service':'pyronix-api','datasetLoaded':ds.GRID_PATH.exists(),'modelLoaded':ds.MODEL_PATH.exists(),'modisLoaded':MODIS_PATH.exists()}

@app.get('/api/metadata')
def get_metadata():
    m=ds.metadata(); model=ds.anomaly_model()
    return {**m,'modelAvailable':model is not None,'modisAvailable':MODIS_PATH.exists(),
            'modelDescription':'Isolation Forest trained on daily 5-degree VIIRS/S-NPP grid-cell aggregates.'}

@app.get('/api/regions')
def regions(): return REGIONS

def filters(region, south, north, west, east, start_date, end_date):
    return dict(region_id=region,south=south,north=north,west=west,east=east,start_date=start_date,end_date=end_date)

@app.get('/api/summary')
def get_summary(region:str='global',mode:str='viirs',south:float|None=None,north:float|None=None,west:float|None=None,east:float|None=None,start_date:str|None=None,end_date:str|None=None):
    return ds.summary(mode=mode,**filters(region,south,north,west,east,start_date,end_date))

@app.get('/api/calendar')
def calendar(region:str='global',mode:str='viirs',south:float|None=None,north:float|None=None,west:float|None=None,east:float|None=None,start_date:str|None=None,end_date:str|None=None):
    df,_=ds.filter_grid(mode=mode,**filters(region,south,north,west,east,start_date,end_date))
    return ds.get_calendar(df)

@app.get('/api/hotspots')
def hotspots(region:str='global',mode:str='viirs',south:float|None=None,north:float|None=None,west:float|None=None,east:float|None=None,start_date:str|None=None,end_date:str|None=None,limit:int=Query(2500,ge=1,le=10000)):
    d=ds.region_map(region,south,north,west,east,start_date,end_date,limit,mode)
    sensor = 'MODIS' if mode == 'modis' else 'VIIRS'
    return [{'id':int(i),'latitude':float(r.latitude),'longitude':float(r.longitude),'frp':float(r.frp),
             'brightness':float(r.brightness),'confidence':str(r.confidence),'date':str(r.acq_date),'time':str(r.acq_time),
             'satellite':str(r.satellite),'sensor':sensor,'daynight':str(r.daynight),'type':int(r.type)} for i,r in enumerate(d.itertuples(index=False))]

@app.get('/api/alerts')
def get_alerts(region:str='global',south:float|None=None,north:float|None=None,west:float|None=None,east:float|None=None,start_date:str|None=None,end_date:str|None=None):
    return ds.alerts(**filters(region,south,north,west,east,start_date,end_date))

@app.get('/api/analytics')
def get_analytics(region:str='global',south:float|None=None,north:float|None=None,west:float|None=None,east:float|None=None,start_date:str|None=None,end_date:str|None=None):
    return ds.analytics(**filters(region,south,north,west,east,start_date,end_date))

@app.post('/api/upload/modis')
async def upload_modis(file:UploadFile=File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(400,'Upload a NASA FIRMS MODIS CSV file.')
    try:
        content=await file.read()
        if not content:
            raise HTTPException(400,'The uploaded CSV is empty.')
        if len(content) > 250 * 1024 * 1024:
            raise HTTPException(413,'CSV exceeds the 250 MB upload limit. Split the NASA FIRMS export into smaller date ranges.')
        from io import BytesIO
        raw=pd.read_csv(BytesIO(content))
        required={'latitude','longitude','acq_date','frp'}
        if not required.issubset(set(raw.columns)):
            raise HTTPException(400,'CSV must contain latitude, longitude, acq_date and frp columns (NASA FIRMS format).')
        raw=raw.dropna(subset=['latitude','longitude','acq_date','frp']).copy()
        if raw.empty:
            raise HTTPException(422,'No valid fire detections were found in the uploaded CSV.')
        for col in ['latitude','longitude','frp']:
            raw[col]=pd.to_numeric(raw[col],errors='coerce')
        raw=raw.dropna(subset=['latitude','longitude','frp'])
        raw=raw[raw.latitude.between(-90,90) & raw.longitude.between(-180,180) & (raw.frp >= 0)]
        if raw.empty:
            raise HTTPException(422,'The CSV contains no valid latitude, longitude and non-negative FRP records.')
        if 'instrument' in raw.columns and not raw.instrument.astype(str).str.upper().str.contains('MODIS').any():
            raise HTTPException(422,'The uploaded FIRMS file does not contain MODIS instrument records.')
        defaults={'brightness':0.0,'confidence':'unknown','acq_time':0,'satellite':'MODIS','instrument':'MODIS','daynight':'U','type':0}
        for col,value in defaults.items():
            if col not in raw.columns: raw[col]=value
        raw['date']=pd.to_datetime(raw.acq_date,errors='coerce').dt.strftime('%Y-%m-%d')
        raw=raw.dropna(subset=['date'])
        raw['lat_cell']=(np.floor(raw.latitude/5)*5).astype(int); raw['lon_cell']=(np.floor(raw.longitude/5)*5).astype(int)
        agg=raw.groupby(['date','lat_cell','lon_cell'],as_index=False).agg(hotspot_count=('frp','size'),frp_sum=('frp','sum'),frp_mean=('frp','mean'),brightness_mean=('brightness','mean'))
        agg['date']=pd.to_datetime(agg.date)
        viirs=ds.grid()[['date','lat_cell','lon_cell','hotspot_count','frp_sum']]
        paired=viirs.merge(agg,on=['date','lat_cell','lon_cell'],suffixes=('_viirs','_modis'))
        if len(paired)<20:
            raise HTTPException(422,f'Only {len(paired)} matching date/grid cells found. Provide overlapping dates and geographic coverage (at least 20 matched cells recommended).')
        if paired.hotspot_count_viirs.nunique() < 3 or paired.hotspot_count_modis.nunique() < 2:
            raise HTTPException(422,'Matched MODIS/VIIRS cells do not contain enough count variation to fit a meaningful calibration.')
        reg=HuberRegressor().fit(np.log1p(paired[['hotspot_count_viirs']]),np.log1p(paired['hotspot_count_modis']))
        pred=reg.predict(np.log1p(paired[['hotspot_count_viirs']]))
        from sklearn.metrics import r2_score
        matched_r2=float(r2_score(np.log1p(paired.hotspot_count_modis),pred))
        if float(reg.coef_[0]) <= 0:
            raise HTTPException(422,'The matched observations did not produce a positive VIIRS-to-MODIS count relationship; calibration was not saved.')
        calibration={'matchedCellDays':int(len(paired)),'countSlope':float(reg.coef_[0]),'countIntercept':float(reg.intercept_),
                     'matchedR2':matched_r2,'fitQuality':'strong' if matched_r2>=0.5 else 'limited; inspect matched R²',
                     'method':'Robust log-linear calibration (Huber regression) on matched 5-degree cell-days.',
                     'modisRows':int(len(raw))}
        agg.to_csv(MODIS_PATH,index=False,compression='gzip')
        sample_cols=[c for c in ['latitude','longitude','frp','brightness','confidence','acq_date','acq_time','satellite','instrument','daynight','type'] if c in raw.columns]
        raw[sample_cols].sample(n=min(60000,len(raw)),random_state=42).to_csv(DATA_DIR/'modis_map_sample.csv.gz',index=False,compression='gzip')
        (DATA_DIR/'modis_calibration.json').write_text(json.dumps(calibration,indent=2))
        ds.modis_grid.cache_clear(); ds.modis_map_points.cache_clear()
        return {'status':'calibrated','calibration':calibration,'message':'MODIS data stored and matched against VIIRS on date and 5-degree grid cells.'}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400,f'Could not process MODIS CSV: {exc}')
