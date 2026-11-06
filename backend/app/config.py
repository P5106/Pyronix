from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
MODEL_PATH = BASE_DIR / 'models' / 'fire_anomaly_model.joblib'
GRID_PATH = DATA_DIR / 'daily_grid.csv.gz'
MAP_PATH = DATA_DIR / 'map_sample.csv.gz'
MODIS_PATH = DATA_DIR / 'modis_daily_grid.csv.gz'

REGIONS = [
    {'id': 'global', 'name': 'Global Overview', 'center': [5, 15], 'zoom': 2, 'bounds': [-90, 90, -180, 180]},
    {'id': 'amazon', 'name': 'Amazon Basin', 'center': [-3.5, -62.2], 'zoom': 4, 'bounds': [-15, 7, -80, -45]},
    {'id': 'california', 'name': 'California, USA', 'center': [37.2, -119.5], 'zoom': 5, 'bounds': [32, 42, -125, -113]},
    {'id': 'australia', 'name': 'SE Australia', 'center': [-35.3, 149.1], 'zoom': 4, 'bounds': [-40, -28, 140, 154]},
    {'id': 'boreal', 'name': 'Siberian Boreal', 'center': [62, 129.7], 'zoom': 4, 'bounds': [50, 72, 105, 160]},
    {'id': 'central-africa', 'name': 'Central Africa', 'center': [-2, 22], 'zoom': 4, 'bounds': [-12, 12, 8, 36]},
    {'id': 'india', 'name': 'India', 'center': [22.5, 79], 'zoom': 4, 'bounds': [6, 36, 67, 98]},
]
