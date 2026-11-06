import { useRef, useState } from 'react';
import { MapPin, Filter, ShieldAlert, Database, UploadCloud, CheckCircle2, AlertTriangle } from 'lucide-react';
import { dateLabel, number } from '../utils/format';

export default function Sidebar({ regions, region, setRegion, startDate, setStartDate, endDate, setEndDate, mode, setMode, metadata, summary, analytics, onUpload, uploading, uploadMessage, customBounds, setCustomBounds }) {
  const fileRef=useRef(null); const [custom,setCustom]=useState(false);
  const selected=regions.find(r=>r.id===region)||regions[0];
  const bounds=customBounds||selected?.bounds||[-90,90,-180,180];
  const updateBound=(index,value)=>{const next=[...bounds];next[index]=Number(value);setCustomBounds(next);};
  const boundsValid=bounds[0]>=-90&&bounds[1]<=90&&bounds[0]<bounds[1]&&bounds[2]>=-180&&bounds[3]<=180&&bounds[2]<bounds[3];
  return <aside className="sidebar">
    <section className="panel control-panel"><div className="section-heading"><MapPin size={16}/><h2>Area of Interest (AOI)</h2></div>
      <label className="field-label">Select monitoring region</label><select value={region} onChange={e=>{setRegion(e.target.value);setCustomBounds(null);}} className="select-field">{regions.map(r=><option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <button className="text-action" onClick={()=>setCustom(v=>!v)}>{custom?'Hide':'Edit'} AOI coordinates</button>
      {custom&&<><div className="bounds-grid">{['South','North','West','East'].map((label,index)=><label key={label}><small>{label}</small><input type="number" step="0.1" value={bounds[index]} onChange={e=>updateBound(index,e.target.value)}/></label>)}</div><div className="bounds-actions"><button className="text-action" onClick={()=>setCustomBounds(null)}>Reset to region</button>{!boundsValid&&<small className="red-text">Enter valid latitude/longitude bounds.</small>}</div></>}
      <div className="date-fields"><div><label className="field-label">From date</label><input type="date" value={startDate} min={metadata?.date_start} max={metadata?.date_end} onChange={e=>setStartDate(e.target.value)}/></div><div><label className="field-label">To date</label><input type="date" value={endDate} min={metadata?.date_start} max={metadata?.date_end} onChange={e=>setEndDate(e.target.value)}/></div></div>
      <p className="muted tiny">Archive coverage: {dateLabel(metadata?.date_start)} — {dateLabel(metadata?.date_end)}</p>
    </section>

    <section className="panel control-panel"><div className="section-heading"><Filter size={16}/><h2>Sensor Pipeline Mode</h2></div>
      <label className="field-label">Active data mode</label><select className="select-field" value={mode} onChange={e=>setMode(e.target.value)}>
        <option value="viirs">VIIRS observations · 375 m</option>
        <option value="modis" disabled={!metadata?.modisAvailable}>MODIS observations · 1 km {!metadata?.modisAvailable?'(upload required)':''}</option>
        <option value="harmonized" disabled={!metadata?.modisAvailable}>Empirical cross-sensor calibration {!metadata?.modisAvailable?'(upload required)':''}</option>
      </select>
      <div className="notice"><AlertTriangle size={15}/><p>{metadata?.modisAvailable?'MODIS archive detected. Matched-cell calibration is available.':'VIIRS has finer nominal sampling than MODIS. Raw sensor counts should not be compared as if they were equivalent. MODIS data is not present in the supplied archive.'}</p></div>
      <div className="upload-area"><input ref={fileRef} type="file" accept=".csv" hidden onChange={e=>e.target.files?.[0]&&onUpload(e.target.files[0])}/><button className="upload-button" onClick={()=>fileRef.current?.click()} disabled={uploading}><UploadCloud size={15}/>{uploading?'Processing MODIS…':'Upload MODIS FIRMS CSV'}</button>{uploadMessage&&<p className="upload-message">{uploadMessage}</p>}<p className="muted tiny">Optional: NASA FIRMS MODIS CSV with latitude, longitude, acq_date and frp columns.</p></div>
    </section>

    <section className="panel warning-panel"><div className="section-heading red"><ShieldAlert size={17}/><h2>Early Warning Status</h2></div>
      <div className="status-row"><span>Latest archive observation</span><strong>{dateLabel(summary?.latestDate)}</strong></div>
      <div className="status-row"><span>Flagged grid cells</span><strong className="red-text">{number(summary?.anomalyCells)}</strong></div>
      <div className="status-row"><span>Anomalous cell share</span><strong className="red-text">{number(summary?.anomalyRate)}%</strong></div>
      <p className="muted tiny">Anomaly scores are statistical indicators, not fire-spread forecasts or official emergency alerts.</p>
    </section>

    <section className="panel dataset-panel"><div className="section-heading"><Database size={16}/><h2>Training Dataset</h2></div>
      <div className="dataset-number">{number(metadata?.source_rows)}</div><p className="muted tiny">VIIRS/S-NPP hotspot records processed</p>
      <div className="dataset-meta"><span>ML model</span><b>{metadata?.model||'Loading…'}</b></div><div className="dataset-meta"><span>Training samples</span><b>{number(metadata?.model_training_samples)}</b></div><div className="dataset-meta"><span>Spatial aggregation</span><b>{metadata?.grid_cell_degrees||5}° grid</b></div>
      <div className="trained-tag"><CheckCircle2 size={13}/> {metadata?.modelAvailable?'Trained model loaded':'Model artifact unavailable'}</div>
      <a className="text-action nasa-link" href="https://firms.modaps.eosdis.nasa.gov/download/" target="_blank" rel="noreferrer">Get official NASA FIRMS archive ↗</a>
    </section>
  </aside>;
}
