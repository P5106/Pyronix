NASA FIRMS source data location

The raw VIIRS/S-NPP archive used to create the bundled processed baseline is not duplicated in this project ZIP. Project metadata records the source member as fire_archive_SV-C2_829122.csv and the source as NASA Earthdata / LANCE FIRMS.

For reproducibility, download historical source data from:
https://firms.modaps.eosdis.nasa.gov/download/

For MODIS/VIIRS API downloads, request a free FIRMS MAP_KEY and use:
backend/scripts/download_firms.py

The bundled baseline is processed VIIRS/S-NPP data only. No MODIS observations are bundled. Obtain an overlapping MODIS Collection 6.1 FIRMS CSV (standard processing recommended for historical analysis) and upload it through the dashboard to enable the cross-sensor match and calibration.

Do not commit FIRMS MAP_KEY credentials or private Earthdata tokens to source control.
