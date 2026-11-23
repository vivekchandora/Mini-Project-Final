# PopScan

India-focused geospatial population explorer.

## Population-data design (reviewed 22 November 2026)

PopScan deliberately separates **place/boundary discovery** from **population estimation**:

1. **Place discovery and boundary:** OpenStreetMap Nominatim. Search results with polygon geometry are ranked ahead of point-only place markers. The selected OSM object is looked up again and validated before analysis.
2. **Current approximate city/area population:** WorldPop Global2 R2025A v1, queried through the official WorldPop API. The API sums the modelled population grid cells falling inside the supplied GeoJSON polygon.
3. **Historical Census context:** The bundled starter reference file contains selected large urban units from Census of India 2011 A-04(I). The reference is shown separately from the WorldPop estimate because Census town/urban-agglomeration boundaries may not match the OSM boundary selected for the current estimate.
4. **Custom polygon analysis:** Uses the same WorldPop population endpoint against the user's own validated polygon.

### Sources and what they mean

- **WorldPop Global2 R2025A v1:** approximately 3 arc-second / 100 m at the equator, annual estimates 2015–2030, CC BY 4.0. It is a modelled gridded population dataset. WorldPop describes R2025A as an alpha release. Its method is top-down random-forest dasymetric redistribution, using census/administrative totals and geospatial covariates such as settlement/built-up information, roads, land cover and topography. It can be affected by the quality and date of input census data, projection assumptions, incomplete covariates and rapid demographic change. It is not a live headcount and does not provide a universal numeric confidence interval for each arbitrary polygon.
- **Census of India 2011:** the Population Finder / Primary Census Abstract provides official historical figures at district, sub-district, town, village and ward levels. The A-04 tables distinguish towns from urban agglomerations. These are not interchangeable units.
- **GHSL GHS-POP R2023A:** an independent European Commission/JRC gridded population dataset for historical epochs and projections. It can be used for a future independent comparison, but it is not currently wired into this app's calculations.
- **OpenStreetMap Nominatim:** a geocoder and mapped-boundary provider, not a population source. Coverage and boundary tagging vary by place. A city point/centroid is not a city boundary.

### City-wise behaviour

Searching Mumbai, Pune, Bengaluru, Delhi or another Indian settlement returns a WorldPop estimate for the exact polygon boundary PopScan successfully resolves. The output names the boundary so users can see whether the result represents a municipal area, town, urban agglomeration, district or another mapped feature.

A small starter file `backend/data/census_2011_city_reference.csv` includes selected large 2011 Census urban units (including Greater Mumbai U.A. and Pune U.A.). These appear as a separate historical reference, never as the current population. **This starter file is not a complete all-India Census database.** Use the importer below with the official Census A-04 Class I–VI workbooks to extend it.

### Import the full Census A-04 city reference tables

1. Download the official A-04 Class I, II, III, IV, V and VI Excel workbooks from the Census of India NADA catalogue.
2. Put the downloaded `.xlsx` files in a folder, e.g. `backend/data/census_downloads`.
3. Install the optional importer dependency: `python -m pip install openpyxl`.
4. From the backend folder run:

   ```powershell
   python scripts/import_census_a04.py data/census_downloads/*.xlsx
   ```

The importer only accepts 2011 rows and writes the consolidated city/urban-agglomeration reference CSV. Check the imported rows against the workbook before production use.

### API

- `GET /api/v1/locations/search?q=Mumbai` — city/settlement matches, polygon-capable matches ranked first.
- `POST /api/v1/population/location` — estimate population for the selected OSM boundary.
- `POST /api/v1/population/custom-area` — estimate population for a custom GeoJSON polygon.
- `GET /api/v1/data-status` — source and dataset status.
- `GET /api/v1/reports/csv` and `/api/v1/reports/pdf` — reports.

The default reference year is **2025**, the latest completed year in the WorldPop series. Users can select 2015–2030. Values for future years are modelled projections/estimates and should be interpreted accordingly.

### Nominatim usage

The shared client throttles requests to at least approximately one request per second in a single process. Set `GEOCODING_USER_AGENT` to an app-identifying value and `GEOCODING_CONTACT_EMAIL` to a contact address. Follow the Nominatim usage policy; do not use the public service for bulk geocoding or high-volume production traffic. For sustained usage, run your own Nominatim instance or use a provider with a suitable service agreement.

### Important limitations

- A correct population total depends on selecting the correct geography. Mumbai city, Greater Mumbai municipal limits and Greater Mumbai urban agglomeration are different geographic units.
- WorldPop's grid is a modelled estimate, not a precise household count. The 100 m label is approximate at the equator; actual ground dimensions vary with latitude.
- PopScan does not currently merge WorldPop and Census values into one number. They are presented as different datasets and years.
- GHSL is documented as a future cross-check but is not downloaded or queried by this build.
- If no valid polygon or validated WorldPop response is available, PopScan returns an error instead of inventing a population.

## Run locally

Backend:

```powershell
cd D:\Downloads\poupscan\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

Frontend (second PowerShell window):

```powershell
cd D:\Downloads\poupscan\frontend
npm.cmd run dev
```

Open http://localhost:5173.
