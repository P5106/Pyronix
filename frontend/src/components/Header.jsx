import { Flame, Info, RadioTower } from 'lucide-react';

const tabs = [
  { id: 'map', label: 'Hotspot Map', icon: RadioTower },
  { id: 'calendar', label: 'Burning Calendar', icon: null },
  { id: 'analytics', label: 'Cross-Sensor Analytics', icon: null },
  { id: 'alerts', label: 'Anomaly Alerts', icon: null },
];
export default function Header({ activeTab, setActiveTab, onMath }) {
  return <header className="topbar">
    <div className="brand"><div className="brand-mark"><Flame size={24}/></div><div><h1>Pyronix <span>| MODIS &amp; VIIRS Fire Harmonizer</span></h1><p>2026 NASA Space Apps Challenge · Burning Activity Calendar &amp; Early Warning</p></div></div>
    <nav className="tabs">{tabs.map((tab, index) => <button key={tab.id} className={activeTab===tab.id?'tab active':'tab'} onClick={()=>setActiveTab(tab.id)}>{tab.id==='map'?<RadioTower size={15}/>:tab.id==='calendar'?<span>▦</span>:tab.id==='analytics'?<span>▥</span>:<span>⚡</span>}{tab.label}</button>)}</nav>
    <button className="math-button" onClick={onMath}><Info size={15}/> Harmonization Math</button>
  </header>;
}
