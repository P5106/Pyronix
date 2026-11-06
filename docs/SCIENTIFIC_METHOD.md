# Scientific method and scope

## Official source and provenance

The baseline data in this package is identified in its metadata as a NASA FIRMS VIIRS Suomi-NPP (SNPP) active-fire archive, `fire_archive_SV-C2_829122.csv`, with 14,652,931 source detections from 2025-01-01 to 2025-10-01. The project bundle contains processed cell-day aggregates and a sampled map file, not the original raw archive. NASA FIRMS archive and API links are documented in the project README.

MODIS observations are not bundled. A user must obtain an overlapping official FIRMS MODIS Collection 6.1 CSV (preferably standard processing for historical research) and upload it before cross-sensor calibration is possible. No synthetic MODIS observations are created.

## Common spatial-temporal aggregation

Both sensors are aggregated by acquisition date and a common 5° latitude/longitude grid cell. A cell-day stores detection count, summed and mean fire radiative power (FRP), and where available brightness and confidence/day-night summaries. MODIS and VIIRS are joined on `(date, lat_cell, lon_cell)`.

This is a regional activity-index harmonization approach. A 5° cell is deliberately coarse; it does not imply pixel-to-pixel equivalence, equal overpass timing, or equivalent sensor detection probability. Sensor resolution and sampling differences remain important.

## Cross-sensor count calibration

For matched MODIS and VIIRS cell-days, the backend fits:

`log(1 + MODIS_count) = intercept + slope × log(1 + VIIRS_count)`

using `HuberRegressor` to reduce sensitivity to extreme cell-days. The app reports the matched cell-day count, slope, intercept and R². A fit is rejected when there are fewer than 20 matched cell-days, insufficient variation, or a non-positive slope. The calibrated mode applies this empirical relationship to VIIRS counts to produce a MODIS-equivalent count index. It does not alter observed FRP.

A positive slope and high R² do not establish physical equivalence. Calibration quality depends on temporal overlap, AOI size, data product version, missing observations, and the chosen aggregation scale.

## Anomaly model

An Isolation Forest is trained on 60,000 samples drawn from the 129,226 VIIRS cell-day aggregates. The model uses log-transformed hotspot count, summed FRP and mean FRP, plus brightness, confidence proxy, night fraction, and sine/cosine month encodings. The bundled model was retrained with 200 trees and a 4% contamination setting. Decision scores are normalized to a 0–100 screening scale; scores of 80 or greater are surfaced for review.

This is unsupervised anomaly screening. No incident labels, fire perimeters, or ground-truth event classifications were supplied, so supervised accuracy metrics are not available and are not fabricated. Model scores are not probabilities of fire danger.

## Calendar and AOI

The burning calendar groups daily AOI totals by chronological calendar month and retains year labels, so multi-year periods are not merged into a single January/February bucket. The monthly 90th-percentile reference is descriptive for the selected AOI and data period, not a universal danger threshold. AOI selection can use preset regions or a custom latitude/longitude bounding box.

## Operational limitations

Active-fire products are affected by overpass schedules, cloud, smoke, fire size, land cover and sensor sensitivity. The baseline period is 2025-01-01 through 2025-10-01, not live fire detections. The map displays a bounded sample of points while summaries and calendar calculations use the full aggregate. This is a research prototype, not an official NASA product, fire-spread forecast, or emergency-response system.
