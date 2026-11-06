import zipfile,pandas as pd,numpy as np,json,joblib,pathlib,os,argparse
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
P=argparse.ArgumentParser(); P.add_argument('archive',help='Path to the NASA FIRMS ZIP archive'); P.add_argument('--project-root',default=str(pathlib.Path(__file__).resolve().parents[2])); args=P.parse_args()
R=pathlib.Path(args.project_root); D=R/'backend/data'; M=R/'backend/models'; D.mkdir(parents=True,exist_ok=True); M.mkdir(parents=True,exist_ok=True)
parts=[]; samples=[]; total=0
with zipfile.ZipFile(args.archive) as z:
 with z.open('fire_archive_SV-C2_829122.csv') as f:
  for ix,c in enumerate(pd.read_csv(f,chunksize=750000)):
   total+=len(c); c['date']=c.acq_date
   c['lat_cell']=(np.floor(c.latitude/5)*5).astype('int16'); c['lon_cell']=(np.floor(c.longitude/5)*5).astype('int16')
   c['conf_num']=c.confidence.map({'l':.35,'n':.6,'h':.9}).fillna(.5); c['night_num']=(c.daynight=='N').astype('int8')
   g=c.groupby(['date','lat_cell','lon_cell'],sort=False).agg(hotspot_count=('frp','size'),frp_sum=('frp','sum'),frp_mean=('frp','mean'),brightness_mean=('brightness','mean'),confidence_mean=('conf_num','mean'),night_count=('night_num','sum')).reset_index()
   parts.append(g)
   if len(samples)<60000:
    n=min(1500,60000-len(samples)); samples.append(c.sample(n=min(n,len(c)),random_state=ix+17)[['latitude','longitude','frp','brightness','confidence','acq_date','acq_time','satellite','instrument','daynight','type']])
   print('chunk',ix+1,'rows',total,'aggregates',sum(len(x) for x in parts),flush=True)
# aggregate across chunks
allg=pd.concat(parts,ignore_index=True)
d=allg.groupby(['date','lat_cell','lon_cell'],as_index=False,sort=False).agg({'hotspot_count':'sum','frp_sum':'sum','frp_mean':'mean','brightness_mean':'mean','confidence_mean':'mean','night_count':'sum'})
d['night_ratio']=d.night_count/d.hotspot_count.clip(lower=1); d['month']=pd.to_datetime(d.date).dt.month
ang=2*np.pi*d.month/12; d['month_sin']=np.sin(ang); d['month_cos']=np.cos(ang)
features=['hotspot_count','frp_sum','frp_mean','brightness_mean','confidence_mean','night_ratio','month_sin','month_cos']
X=d[features].replace([np.inf,-np.inf],np.nan).fillna(0)
for col in ['hotspot_count','frp_sum','frp_mean']: X[col]=np.log1p(X[col].clip(lower=0))
# Keep model training bounded, but draw training rows across the complete processed period.
train=X.sample(n=min(60000,len(X)),random_state=42)
pipe=Pipeline([('scale',StandardScaler()),('model',IsolationForest(n_estimators=200,contamination=.04,random_state=42,n_jobs=-1))]); pipe.fit(train)
scores=-pipe.decision_function(X); lo,hi=np.quantile(scores,[.05,.99]); d['anomaly_score']=np.clip((scores-lo)/(hi-lo+1e-9)*100,0,100).round(1); d['is_anomaly']=d.anomaly_score>=80
# remove derived training-only date cols
D.mkdir(exist_ok=True); d.to_csv(D/'daily_grid.csv.gz',index=False,compression='gzip')
sm=pd.concat(samples,ignore_index=True).drop_duplicates(); sm.to_csv(D/'map_sample.csv.gz',index=False,compression='gzip')
joblib.dump({'pipeline':pipe,'features':features,'score_p05':float(lo),'score_p99':float(hi),'training_rows':len(train),'source_hotspots':total,'model_name':'IsolationForest'},M/'fire_anomaly_model.joblib',compress=3)
meta={'source_file':'fire_archive_SV-C2_829122.csv','source_sensor':'VIIRS S-NPP (SNPP)','source_provider':'NASA Earthdata / LANCE FIRMS','source_product':'VIIRS 375 m active fire, Suomi-NPP (SNPP)','source_url':'https://firms.modaps.eosdis.nasa.gov/download/','modis_source_required':True,'modis_dataset_included':False,'source_rows':total,'date_start':d.date.min(),'date_end':d.date.max(),'grid_cell_degrees':5,'daily_grid_rows':len(d),'map_sample_rows':len(sm),'model':'IsolationForest','model_training_samples':len(train),'model_estimators':200,'model_contamination':0.04,'anomaly_threshold':80,'features':features,'training_note':'Trained on supplied VIIRS/S-NPP archive only. Anomaly detection is not MODIS-to-VIIRS cross-sensor calibration.'}
(D/'training_metadata.json').write_text(json.dumps(meta,indent=2)); print('DONE',json.dumps(meta),flush=True)
for p in [D/'daily_grid.csv.gz',D/'map_sample.csv.gz',M/'fire_anomaly_model.joblib']: print(p,p.stat().st_size,flush=True)
