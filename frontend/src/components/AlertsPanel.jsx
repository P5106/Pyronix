import { AlertOctagon, MapPin, CalendarClock } from 'lucide-react';
import { number } from '../utils/format';
export default function AlertsPanel({ alerts, loading }) {
 return <section className="content-panel"><div className="panel-topline"><div><h2>Unusual Burning Activity</h2><p>Isolation Forest outlier flags from daily VIIRS grid-cell observations</p></div><span className="data-pill warning">{alerts.length} flagged records</span></div>
  <div className="alert-explainer"><AlertOctagon size={18}/><p>These are statistically unusual observations relative to the model's training distribution. They are screening signals for investigation, not verified wildfire incidents or operational warnings.</p></div>
  {loading&&<p className="muted">Loading anomaly records…</p>}
  {!loading&&alerts.length===0&&<div className="empty-state"><h3>No flagged cell-days in this selection</h3><p>Try a different region or date range.</p></div>}
  <div className="alert-list">{alerts.map((a,i)=><article className="alert-item" key={`${a.date}-${a.latitude}-${i}`}><div className="alert-score"><b>{number(a.score)}</b><small>score</small></div><div className="alert-body"><div className="alert-title"><b>{a.severity} anomaly</b><span>{a.date}</span></div><p><MapPin size={13}/> {a.latitude.toFixed(1)}°, {a.longitude.toFixed(1)}° <span>·</span> {number(a.hotspotCount)} hotspots <span>·</span> {number(a.frp)} MW FRP</p></div><CalendarClock size={16} className="muted"/></article>)}</div>
 </section>;
}
