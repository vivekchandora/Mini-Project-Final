import { useState } from 'react';
import axios from 'axios';
import {
  MapContainer,
  TileLayer,
  FeatureGroup,
} from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet-draw';

const API = '';

export default function App() {
  const [geo, setGeo] = useState<any>(null);
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const name = 'Custom selected area';

  async function analyse() {
    if (!geo) return;
    setBusy(true);
    setErr('');
    setRes(null);
    try {
      const response = await axios.post(`${API}/api/v1/population/custom-area`, {
        geojson: geo,
        year: 2026,
        location: name,
      });
      setRes(response.data);
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      setErr(
        typeof detail === 'string'
          ? detail
          : detail?.message || 'Population data unavailable. No population value was fabricated.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header>
        <div className="logo">P<span>OUPSCAN</span></div>
        <small>INDIA · POPULATION INTELLIGENCE</small>
      </header>

      <section className="hero">
        <div>
          <label>GEOSPATIAL POPULATION EXPLORER</label>
          <h1>Understand places.<br /><i>Measure population.</i></h1>
          <p>Draw a custom boundary on the map to request a data-backed population estimate.</p>
        </div>
      </section>

      <div className="layout">
        <section className="mapbox">
          <div className="map">
            <MapContainer center={[22.8, 79]} zoom={4.5}>
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <FeatureGroup>
                <EditControl
                  position="topright"
                  onCreated={(event: any) => {
                    setGeo(event.layer.toGeoJSON().geometry);
                    setRes(null);
                    setErr('');
                  }}
                  onEdited={(event: any) =>
                    event.layers.eachLayer((layer: any) => setGeo(layer.toGeoJSON().geometry))
                  }
                  onDeleted={() => {
                    setGeo(null);
                    setRes(null);
                    setErr('');
                  }}
                  draw={{
                    rectangle: false,
                    circle: false,
                    circlemarker: false,
                    marker: false,
                    polyline: false,
                    polygon: { allowIntersection: false },
                  }}
                />
              </FeatureGroup>
            </MapContainer>
          </div>
          <p className="mapcaption">Draw a polygon using the map toolbar. Map tiles © OpenStreetMap.</p>
        </section>

        <aside>
          <label>ANALYSIS PANEL</label>
          <h2>Population estimate</h2>
          <div className="selected">
            <small>SELECTED AREA</small>
            <b>{name}</b>
            <p>{busy ? 'Calculating population data…' : geo ? 'Custom boundary selected' : res ? 'Custom boundary analysed' : 'Draw a polygon on the map to begin'}</p>
          </div>
          <button className="go" disabled={!geo || busy} onClick={analyse}>
            {busy ? 'Analysing…' : 'Analyse custom boundary ↗'}
          </button>
          {err && <div className="error">{err}</div>}
          {res && (
            <div className="result">
              <small>MODELLED POPULATION ESTIMATE</small>
              <strong>{Number(res.estimated_population).toLocaleString('en-IN')}</strong>
              <p>Boundary: Custom selected area</p>
              <p>Area: {Number(res.area_sq_km).toLocaleString('en-IN')} km²</p>
              <p>Density: {Number(res.population_density).toLocaleString('en-IN')} people/km²</p>
              <p>Reference year: {res.reference_year}</p>
              <p>Source: {res.data_source}</p>
              <p>{res.confidence || 'Modelled estimate; not an official Census count or live headcount.'}</p>
              {res.source_url && <p><a href={res.source_url} target="_blank" rel="noreferrer">Dataset documentation</a></p>}
              <a href={`${API}/api/v1/reports/csv?location=${encodeURIComponent(name)}&population=${res.estimated_population}&area=${res.area_sq_km}`}>CSV</a>
              {' · '}
              <a href={`${API}/api/v1/reports/pdf?location=${encodeURIComponent(name)}&population=${res.estimated_population}&area=${res.area_sq_km}`}>PDF report</a>
            </div>
          )}
          <div className="integrity">
            <b>Data integrity first</b>
            <p>Population estimates come from a validated gridded dataset. They are not live headcounts or official Census counts. If a boundary or source response cannot be validated, Poupscan explains why it cannot return a figure.</p>
          </div>
        </aside>
      </div>
      <footer>POUPSCAN MVP 1.0 <span>Estimates are not official census counts.</span></footer>
    </div>
  );
}
