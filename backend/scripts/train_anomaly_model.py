"""Retrain the VIIRS cell-day anomaly detector from the processed NASA FIRMS grid."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
MODEL_DIR = ROOT / 'models'
GRID = DATA / 'daily_grid.csv.gz'
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = ['hotspot_count', 'frp_sum', 'frp_mean', 'brightness_mean',
            'confidence_mean', 'night_ratio', 'month_sin', 'month_cos']

def main():
    if not GRID.exists():
        raise SystemExit(f'Missing {GRID}. Run prepare_dataset.py first.')
    df = pd.read_csv(GRID, compression='gzip')
    missing = sorted(set(FEATURES) - set(df.columns))
    if missing:
        raise SystemExit(f'Dataset is missing model features: {missing}')
    X = df[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0).copy()
    for col in ['hotspot_count', 'frp_sum', 'frp_mean']:
        X[col] = np.log1p(X[col].clip(lower=0))
    n = min(60000, len(X))
    train = X.sample(n=n, random_state=42) if len(X) > n else X
    pipeline = Pipeline([
        ('scale', StandardScaler()),
        ('model', IsolationForest(n_estimators=200, contamination=0.04,
                                  random_state=42, n_jobs=-1))
    ])
    pipeline.fit(train)
    raw_scores = -pipeline.decision_function(X)
    lo, hi = np.quantile(raw_scores, [0.05, 0.99])
    scores = np.clip((raw_scores - lo) / (hi - lo + 1e-12) * 100, 0, 100)
    df['anomaly_score'] = np.round(scores, 1)
    df['is_anomaly'] = df['anomaly_score'] >= 80
    df.to_csv(GRID, index=False, compression='gzip')
    artifact = {
        'pipeline': pipeline, 'features': FEATURES,
        'score_p05': float(lo), 'score_p99': float(hi),
        'training_rows': int(n), 'source_hotspots': None,
        'model_name': 'IsolationForest', 'n_estimators': 200,
        'contamination': 0.04, 'threshold': 80
    }
    joblib.dump(artifact, MODEL_DIR / 'fire_anomaly_model.joblib', compress=3)
    meta_path = DATA / 'training_metadata.json'
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({
        'model': 'IsolationForest', 'model_training_samples': int(n),
        'model_estimators': 200, 'model_contamination': 0.04,
        'anomaly_threshold': 80,
        'features': FEATURES,
        'training_note': 'Unsupervised Isolation Forest retrained from NASA FIRMS VIIRS/S-NPP daily 5-degree cell-day aggregates. This is anomaly screening, not MODIS-to-VIIRS calibration.'
    })
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps({'status': 'trained', 'rows': len(df), 'training_samples': n,
                      'anomalies': int(df.is_anomaly.sum()),
                      'date_start': str(df.date.min()), 'date_end': str(df.date.max())}, indent=2))

if __name__ == '__main__':
    main()
