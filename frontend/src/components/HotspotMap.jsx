import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import { Download, Crosshair } from 'lucide-react';

function MapViewport({center,zoom}) { const map=useMap(); useEffect(()=>{map.setView(center,zoom,{animate:true});},[map,center,zoom]); return null; }
export default function HotspotMap({ regionInfo, hotspots, alerts=[], mode='viirs', loading, onExport }) {
 const center=regionInfo?.center||[5,15]; const zoom=regionInfo?.zoom||2;
 return <section className="content-panel map-panel"><div className="panel-topline"><div><h2>Active Hotspots Map — {regionInfo?.name||'Global'}</h2><p>{mode==='modis'?'Sampled MODIS active-fire detections':'Sampled VIIRS active-fire detections'} · 5° regional analysis grid{mode==='harmonized'?' · MODIS-equivalent count index':''}</p></div><button className="outline-button" onClick={onExport}><Download size={14}/> Export GeoJSON</button></div>
  <div className="map-legend"><span><i className="legend-dot viirs"/> {mode==='modis'?'MODIS':'VIIRS / S-NPP'} detections</span><span><i className="legend-dot anomaly"/> Statistical anomaly cell</span><span className="map-count">{hotspots.length.toLocaleString()} plotted records{loading?' · updating…':''}</span></div>
  <div className="map-frame"><MapContainer center={center} zoom={zoom} scrollWheelZoom className="leaflet-map"><MapViewport center={center} zoom={zoom}/><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
   {alerts.map((a,i)=><CircleMarker key={`anomaly-${i}`} center={[a.latitude,a.longitude]} radius={11} pathOptions={{color:'#ef4444',fillColor:'#ef4444',fillOpacity:.12,weight:2,dashArray:'4 4'}}><Popup><div className="popup-content"><b>Statistical anomaly · {a.severity}</b><span>Date: {a.date}</span><span>Model score: {a.score}</span><span>Hotspots: {a.hotspotCount}</span><span>FRP: {a.frp} MW</span></div></Popup></CircleMarker>)}
   {hotspots.map((spot,i)=><CircleMarker key={`${spot.id}-${i}`} center={[spot.latitude,spot.longitude]} radius={spot.frp>100?7:spot.frp>30?5:3} pathOptions={{color:'#fb923c',fillColor:'#ef4444',fillOpacity:.65,weight:1}}><Popup><div className="popup-content"><b>{spot.sensor} · {spot.satellite}</b><span>Date: {spot.date}</span><span>FRP: {Number(spot.frp).toFixed(2)} MW</span><span>Brightness: {Number(spot.brightness).toFixed(1)} K</span><span>Confidence: {spot.confidence}</span><span>Day/Night: {spot.daynight}</span></div></Popup></CircleMarker>)}
  </MapContainer>{hotspots.length===0&&<div className="map-empty"><Crosshair size={22}/><span>No sampled detections in this AOI/date range.</span></div>}</div>
  <p className="map-footnote">Map markers are a bounded sample for browser performance; all 14.65 million source detections contribute to the processed regional statistics.</p>
 </section>;
}
