import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import KpiCards from './components/KpiCards';
import HotspotMap from './components/HotspotMap';
import BurningCalendar from './components/BurningCalendar';
import Analytics from './components/Analytics';
import AlertsPanel from './components/AlertsPanel';
import MathModal from './components/MathModal';
import { apiGet, uploadModis } from './services/api';

const emptySummary={hotspotCount:0,frpTotal:0,activeCells:0,anomalyCells:0,anomalyRate:0};
export default function App(){
 const [regions,setRegions]=useState([]); const [region,setRegion]=useState('amazon'); const [activeTab,setActiveTab]=useState('map');
 const [mode,setMode]=useState('viirs'); const [startDate,setStartDate]=useState(''); const [endDate,setEndDate]=useState('');
 const [customBounds,setCustomBounds]=useState(null);
 const [metadata,setMetadata]=useState(null); const [summary,setSummary]=useState(emptySummary); const [hotspots,setHotspots]=useState([]); const [calendar,setCalendar]=useState([]); const [analytics,setAnalytics]=useState(null); const [alerts,setAlerts]=useState([]);
 const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [showMath,setShowMath]=useState(false); const [uploading,setUploading]=useState(false); const [uploadMessage,setUploadMessage]=useState('');
 const selectedRegion=useMemo(()=>{const base=regions.find(r=>r.id===region)||regions[0];if(!base||!customBounds)return base;const [south,north,west,east]=customBounds;return {...base,bounds:customBounds,center:[(south+north)/2,(west+east)/2],zoom:4,name:`Custom AOI · ${base.name}`};},[regions,region,customBounds]);
 const load=useCallback(async()=>{
  if(startDate&&endDate&&startDate>endDate){setError('Start date must be earlier than or equal to end date.');return;}
  if(customBounds&&(customBounds[0]>=customBounds[1]||customBounds[0]<-90||customBounds[1]>90||customBounds[2]>=customBounds[3]||customBounds[2]<-180||customBounds[3]>180)){setError('AOI coordinates are invalid. Check south/north and west/east bounds.');return;}
  setLoading(true);setError('');
  const params={region,mode,start_date:startDate,end_date:endDate,...(customBounds?{south:customBounds[0],north:customBounds[1],west:customBounds[2],east:customBounds[3]}:{})};
  try{
   const [sum,points,cal,ana,warning,meta]=await Promise.all([
    apiGet('/api/summary',params),apiGet('/api/hotspots',{...params,limit:2500}),apiGet('/api/calendar',params),apiGet('/api/analytics',params),apiGet('/api/alerts',params),apiGet('/api/metadata')
   ]);
   setSummary(sum);setHotspots(points);setCalendar(cal);setAnalytics(ana);setAlerts(warning);setMetadata(meta);
  }catch(e){setError(e.message||'Could not load data. Check that the API server is running.');}
  finally{setLoading(false);}
 },[region,mode,startDate,endDate,customBounds]);
 useEffect(()=>{apiGet('/api/regions').then(setRegions).catch(e=>setError(e.message));apiGet('/api/metadata').then(setMetadata).catch(()=>{});},[]);
 useEffect(()=>{load();},[load]);
 const handleUpload=async file=>{
  setUploading(true);setUploadMessage('');
  try{const result=await uploadModis(file);setUploadMessage(`Calibration complete · ${result.calibration.matchedCellDays.toLocaleString()} matched cell-days`);await load();}
  catch(e){setUploadMessage(`Upload failed: ${e.message}`);}
  finally{setUploading(false);}
 };
 const exportGeoJSON=()=>{
  const featureCollection={type:'FeatureCollection',name:'Pyronix_VIIRS_Hotspots',features:hotspots.map(p=>({type:'Feature',geometry:{type:'Point',coordinates:[p.longitude,p.latitude]},properties:{sensor:p.sensor,satellite:p.satellite,date:p.date,frp_mw:p.frp,brightness_k:p.brightness,confidence:p.confidence,daynight:p.daynight}}))};
  const blob=new Blob([JSON.stringify(featureCollection,null,2)],{type:'application/geo+json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`pyronix-${region}-hotspots.geojson`;a.click();URL.revokeObjectURL(url);
 };
 return <div className="app-shell">
  <Header activeTab={activeTab} setActiveTab={setActiveTab} onMath={()=>setShowMath(true)}/>
  <main className="main-layout">
   <Sidebar regions={regions} region={region} setRegion={setRegion} startDate={startDate} setStartDate={setStartDate} endDate={endDate} setEndDate={setEndDate} mode={mode} setMode={setMode} metadata={metadata} summary={summary} analytics={analytics} onUpload={handleUpload} uploading={uploading} uploadMessage={uploadMessage} customBounds={customBounds} setCustomBounds={setCustomBounds}/>
   <section className="workspace">
    <div className="workspace-heading"><div><p className="eyebrow">SATELLITE FIRE INTELLIGENCE</p><h2>{activeTab==='map'?'Monitoring overview':activeTab==='calendar'?'Seasonal burning patterns':activeTab==='analytics'?'Sensor harmonization':'Early warning signals'}</h2><p>Area of interest: <b>{selectedRegion?.name||'Loading region…'}</b> · {metadata?.source_sensor||'Loading source…'}</p></div><button className="refresh-button" onClick={load} disabled={loading}><RefreshCw size={14} className={loading?'spin':''}/> Refresh data</button></div>
    {error&&<div className="error-banner"><AlertTriangle size={16}/><span>{error}</span></div>}
    <KpiCards summary={summary} mode={mode}/>
    {activeTab==='map'&&<HotspotMap regionInfo={selectedRegion} hotspots={hotspots} alerts={alerts} mode={mode} loading={loading} onExport={exportGeoJSON}/>}
    {activeTab==='calendar'&&<BurningCalendar data={calendar} loading={loading}/>}
    {activeTab==='analytics'&&<Analytics data={analytics} metadata={metadata} mode={mode}/>}
    {activeTab==='alerts'&&<AlertsPanel alerts={alerts} loading={loading}/>}
    <footer className="app-footer"><span>PYRONIX · Research prototype</span><span>NASA FIRMS active-fire archive · VIIRS/S-NPP</span><span>Not an official NASA operational warning product</span></footer>
   </section>
  </main>
  <MathModal open={showMath} onClose={()=>setShowMath(false)} metadata={metadata} calibration={analytics?.calibration}/>
 </div>;
}
