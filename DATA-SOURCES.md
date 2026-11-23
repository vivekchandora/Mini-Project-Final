# PopScan — population data research notes

Research snapshot: 22 November 2026.

## Recommended hierarchy

| Need | Primary source | Role |
|---|---|---|
| Recent population estimate for any selected Indian city polygon | WorldPop Global2 R2025A v1 | Main modelled gridded population estimate |
| Historical official city/town/ward count | Census of India PCA / A-04 | Historical benchmark; keep its unit and year visible |
| Independent spatial cross-check | European Commission GHSL GHS-POP R2023A | Not integrated yet |
| Search and boundary geometry | OpenStreetMap Nominatim | Geocoding and boundary discovery only |

## Why not hard-code city totals?

A city label does not identify a unique statistical geography. For example, Mumbai can refer to the municipal corporation, a city/town unit, a wider urban agglomeration or a metropolitan region. A fixed population value attached to the string "Mumbai" can therefore be wrong even if that value is accurate for a different boundary. PopScan instead calculates from the polygon selected and labels that polygon.

## WorldPop

WorldPop's v3 API accepts a GeoJSON Polygon or MultiPolygon in longitude/latitude (EPSG:4326) and a year between 2015 and 2030. Its population endpoint returns people, area and density. The API documentation shows `WorldPop Global2 R2025A, 100 m` in its example response.

WorldPop's release statement explains that Global2 uses a top-down random-forest dasymetric redistribution approach. The public R2025A release is described as alpha and may be revised. Its estimates draw on administrative/census totals and geospatial covariates, so quality depends on source data and modelling assumptions. A 100 m grid should not be interpreted as a precise count at every address or building.

## Census of India

The Population Finder is based on Primary Census Abstract tables and supports district, sub-district, town, village and ward granularity. The Census tables catalogue also exposes A-04 town and urban-agglomeration tables, with a separate unit type. The bundled reference CSV is a small starter list, not a full national town database. The included importer can consolidate official Class I–VI A-04 workbooks after the user downloads them from the Census catalogue.

## GHSL

The European Commission Joint Research Centre GHS-POP R2023A is a multitemporal population grid, with residential population in grid cells and epochs from 1975 to 2030. Its inputs and spatial redistribution differ from WorldPop. It is suitable as an independent comparison, but this build does not claim to use it.

## URLs

- WorldPop API docs: https://api.worldpop.org/v3/documentation
- WorldPop API about/method and citation: https://api.worldpop.org/v3/about
- WorldPop Global2 release statement: https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf
- WorldPop dataset listing: https://hub.worldpop.org/geodata/listing?id=135
- Census of India Population Finder: https://censusindia.gov.in/census.website/data/population-finder
- Census of India tables catalogue: https://censusindia.gov.in/census.website/en/data/tables
- Census A-04 Class I catalogue record: https://censusindia.gov.in/nada/index.php/catalog/42876
- Nominatim Search API: https://nominatim.org/release-docs/latest/api/Search/
- Nominatim usage policy: https://operations.osmfoundation.org/policies/nominatim/
- GHSL GHS-POP R2023A: https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php
