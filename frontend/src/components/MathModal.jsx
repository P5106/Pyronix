import { X, Sigma, Info } from 'lucide-react';
export default function MathModal({ open, onClose, metadata, calibration }) {
 if(!open)return null;
 return <div className="modal-backdrop" onClick={onClose}><div className="modal-card" onClick={e=>e.stopPropagation()}><div className="modal-title"><div><Sigma size={18}/><h2>Hotspot Harmonization Mathematics</h2></div><button onClick={onClose} aria-label="Close"><X size={18}/></button></div>
  <p>Pyronix separates two tasks: detecting unusual burning activity in the supplied record, and estimating cross-sensor differences when matched MODIS data is available.</p>
  <h3>1. VIIRS anomaly detection</h3><div className="formula">score(x) = − IsolationForest.decision_function(x)</div><p>Features include log hotspot count, log summed FRP, mean FRP, mean brightness, confidence, night fraction and seasonal month encoding. Scores are normalized against the training-score distribution; high scores indicate unusual cell-days.</p>
  <h3>2. Optional empirical MODIS calibration</h3><div className="formula">log(1 + MODIS count) = β₀ + β₁ · log(1 + VIIRS count)</div><p>When a MODIS FIRMS CSV is uploaded, the backend matches date + 5° grid cells and fits a robust Huber regression. This estimates an archive-specific relationship; it does not claim physical equivalence at individual pixel scale.</p>
  <div className="science-note"><Info size={15}/><p>Current model: {metadata?.model||'IsolationForest'} trained on {Number(metadata?.model_training_samples||0).toLocaleString()} aggregated samples from {Number(metadata?.source_rows||0).toLocaleString()} VIIRS records. {calibration?'MODIS calibration has been fitted.':'No MODIS calibration is currently fitted.'}</p></div>
  <button className="primary-button modal-close" onClick={onClose}>Close explanation</button>
 </div></div>;
}
