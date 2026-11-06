# PYRONIX — MODIS–VIIRS Fire Activity Harmonizer

A modular React + FastAPI research prototype for exploring NASA FIRMS active-fire observations, building a burning-activity calendar, screening unusual fire activity, and empirically comparing MODIS with VIIRS where overlapping observations are available.

## What is included

- **React/Vite dashboard** retaining the supplied Pyronix dark UI: map, AOI controls, burning calendar, sensor analytics, anomaly panel and method modal.
- **FastAPI backend** with separate data-service and route modules.
- **NASA FIRMS VIIRS/S-NPP baseline**: 14,652,931 source detections represented by 129,226 daily 5° cell aggregates and a 30,000-point map sample.
- **Retrained Isolation Forest**: 200 trees, 60,000 training samples, eight cell-day features, 0–100 screening score. The included model was retrained from the supplied processed NASA FIRMS VIIRS grid during project preparation.
- **MODIS ingestion + cross-sensor fit**: upload an official FIRMS MODIS CSV. The backend aggregates MODIS using the same UTC acquisition date and 5° cell key, matches cell-days to VIIRS, and fits a robust log-count relationship using Huber regression.
- **Export**: map detections as GeoJSON.
- **AOI controls**: choose a preset region or enter a custom bounding box; filter by date.

> **Important data limitation:** the project ZIP contains the processed VIIRS data and trained model, but does not contain the original 264 MB raw VIIRS archive or a MODIS archive. Therefore the VIIRS dashboard works immediately. True MODIS–VIIRS calibration becomes available only after you download and upload an overlapping NASA FIRMS MODIS CSV. The project deliberately does not invent MODIS observations or claim that VIIRS-only anomaly detection is cross-sensor harmonization.

## Project structure

```text
pyronix_build/
├── frontend/
│   ├── src/
│   │   ├── components/       # Header, Sidebar, KPIs, Map, Calendar, Analytics, Alerts, Modal
│   │   ├── services/api.js   # API client
│   │   ├── utils/format.js   # formatting helpers
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI endpoints + MODIS upload/calibration
│   │   ├── data_service.py   # filtering, AOI summaries, calendar, map, alerts
│   │   └── config.py
│   ├── data/                 # processed VIIRS grid + map sample + metadata
│   ├── models/               # trained Isolation Forest artifact
│   ├── scripts/
│   │   ├── download_firms.py # official NASA FIRMS API downloader
│   │   ├── prepare_dataset.py# raw VIIRS archive → grid + map sample + model
│   │   └── train_anomaly_model.py # retrain from processed grid
│   └── requirements.txt
├── docs/SCIENTIFIC_METHOD.md
└── start_backend.bat / start_frontend.bat
```

## Run on Windows 11

Install Python 3.11+ and Node.js 20+ (Node 22/24 is fine).

### 1. Backend terminal

```powershell
cd pyronix_build\backend
py -m pip install -r requirements.txt
py run.py
```

Backend: `http://127.0.0.1:8000`  
API health: `http://127.0.0.1:8000/api/health`  
Interactive API docs: `http://127.0.0.1:8000/docs`

### 2. Frontend terminal

```powershell
cd pyronix_build\frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

If the backend is hosted on a different address, copy `frontend/.env.example` to `frontend/.env` and update `VITE_API_BASE`.

### One-click Windows launchers

Run `start_backend.bat` and `start_frontend.bat` in separate terminals. The backend launcher uses the active Python installation and installs the listed requirements if needed; it does not create a virtual environment.

## Obtain the missing MODIS observations from NASA (required for true harmonization)

NASA FIRMS is the authoritative source used by this prototype:

- FIRMS archive download: https://firms.modaps.eosdis.nasa.gov/download/
- FIRMS active-fire product overview: https://firms.modaps.eosdis.nasa.gov/content/active_fire/
- FIRMS Area API documentation: https://firms2.modaps.eosdis.nasa.gov/api/area/
- Request a free FIRMS MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key

The supplied VIIRS baseline spans **2025-01-01 through 2025-10-01**. To fit a meaningful comparison, download MODIS observations for the same overlapping dates and preferably the same geographic AOI. Use standard processing (`MODIS_SP`) for historical scientific analysis when available; NASA notes that near-real-time data can later be replaced by standard science-quality data.

Example: download MODIS observations for the Amazon AOI over the same period (replace the key with your own private MAP_KEY):

```powershell
cd pyronix_build\backend
py -m pip install -r requirements.txt
$env:NASA_FIRMS_MAP_KEY='YOUR_MAP_KEY'
py scripts\download_firms.py --sensor MODIS --area=-80,-15,-45,7 --start 2025-01-01 --end 2025-10-01 --output ..\source_data\modis_amazon_2025.csv
```

The script requests at most five days per FIRMS API transaction and combines the CSV responses. For a large region, use smaller AOIs/date ranges first. Keep your MAP_KEY private; do not commit it to GitHub. The script accepts the key from the `NASA_FIRMS_MAP_KEY` environment variable so it does not need to be placed in the command-line arguments.

Then open the dashboard, choose the corresponding AOI, and use **Upload MODIS FIRMS CSV**. A successful fit requires at least 20 matched date/grid cell-days and meaningful count variation in both sensors. The Analytics tab displays matched sample count, slope, intercept and R². If the match count is too low, use a larger overlapping AOI or longer overlapping date range.

Alternatively, use the NASA archive website to request a MODIS Collection 6.1 CSV export and upload that file directly. Archive requests may require Earthdata Login and are processed asynchronously by NASA.

## Retrain the ML anomaly model

The model included in the project has already been retrained from `backend/data/daily_grid.csv.gz`:

```powershell
cd pyronix_build\backend
py -m pip install -r requirements.txt
py scripts\train_anomaly_model.py
```

To regenerate the VIIRS aggregates from the original NASA FIRMS VIIRS/S-NPP archive ZIP, place the archive in `source_data/` and run:

```powershell
py scripts\prepare_dataset.py ..\source_data\DL_FIRE_SV-C2_829122.zip
```

The raw 264 MB archive is not included in this ZIP. `prepare_dataset.py` expects the CSV member `fire_archive_SV-C2_829122.csv` inside the archive.

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | API + dataset + model health |
| `GET /api/metadata` | Source coverage, model metadata, MODIS availability |
| `GET /api/regions` | Preset AOIs |
| `GET /api/summary` | AOI hotspot/FRP/anomaly KPIs |
| `GET /api/hotspots` | Bounded map sample |
| `GET /api/calendar` | Chronological month-year burning activity |
| `GET /api/alerts` | Statistical anomaly cell-days |
| `GET /api/analytics` | VIIRS/MODIS totals and calibration diagnostics |
| `POST /api/upload/modis` | Validate, aggregate, match and calibrate MODIS CSV |

## Scientific interpretation and limitations

- Active-fire pixels are satellite detections, not a complete inventory of all fires. Cloud, smoke, overpass timing, fire size, land cover and sensor sensitivity affect detection.
- The 5° grid is intentionally coarse and suitable only for regional historical screening. It is not pixel-level geolocation harmonization.
- The robust log-linear calibration is an empirical count relationship fitted from matched cell-days. It is not a NASA operational cross-calibration product. FRP remains sensor-observed and is not transformed by the count calibration.
- Isolation Forest is unsupervised. There are no incident labels or ground-truth perimeters in the supplied dataset; accuracy, precision and recall are therefore not claimed.
- A statistical anomaly is not a verified wildfire, fire-spread forecast, official warning or dispatch instruction.
- The bundled baseline is historical and does not provide live fire detections. NASA FIRMS NRT/API feeds require a user-supplied MAP_KEY for automated retrieval.

See [`docs/SCIENTIFIC_METHOD.md`](docs/SCIENTIFIC_METHOD.md) for methodology.
#   P y r o n i x  
 