import { Flame, Activity, Grid3X3, Zap } from 'lucide-react';
import { shortNumber, number } from '../utils/format';
export default function KpiCards({ summary, mode = 'viirs' }) {
 const cards=[
  {label:'Hotspot observations',value:shortNumber(summary?.hotspotCount),unit:'records in selected AOI',icon:Flame,tone:'orange'},
  {label:'Fire Radiative Power',value:shortNumber(summary?.frpTotal),unit:mode==='harmonized'?'MW · raw VIIRS FRP':'MW · observed FRP',icon:Activity,tone:'amber'},
  {label:'Active grid cells',value:number(summary?.activeCells),unit:'5° daily grid cells',icon:Grid3X3,tone:'blue'},
  {label:'Anomaly flags',value:number(summary?.anomalyCells),unit:`${number(summary?.anomalyRate)}% of cell-days`,icon:Zap,tone:'red'},
 ];
 return <div className="kpi-grid">{cards.map(c=><div className="kpi-card" key={c.label}><div className={`kpi-icon ${c.tone}`}><c.icon size={18}/></div><div><p>{c.label}</p><strong>{c.value}</strong><small>{c.unit}</small></div></div>)}</div>;
}
