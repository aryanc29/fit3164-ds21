// a11y-markers.js — recolour station markers using the selected colour-blind palette
(function () {
  const API_BASE = '/api';

  // -------- robust access to map + layer (works even if not on window.*) --------
  function getMap() {
    return window.weatherMap || (typeof weatherMap !== 'undefined' ? weatherMap : null);
  }
  function getMarkersLayer() {
    return window.markersLayer || (typeof markersLayer !== 'undefined' ? markersLayer : null);
  }

  // ----------------------------- helpers -----------------------------
  function getSelectedPaletteName() {
    const el = document.getElementById('colour-scale');
    return el && el.value ? el.value : 'Viridis';
  }
  function getPaletteArray(name) {
    const fallback = ["#440154","#3b528b","#21918c","#5ec962","#fde725"]; // Viridis
    if (window.A11Y && A11Y.CB_PALETTES && A11Y.CB_PALETTES[name]) return A11Y.CB_PALETTES[name];
    return fallback;
  }
  function colourFromPalette(pal, t) {
    const clamped = Math.max(0, Math.min(1, t));
    const idx = Math.round(clamped * (pal.length - 1));
    return pal[idx];
  }
  function currentMetric() {
    const sel = document.getElementById('mapMetric');
    return sel && sel.value ? sel.value : 'record_count';
  }
  function valueForMetric(station, metric) {
    if (metric === 'avg_rainfall') return Number(station.avg_rainfall ?? 0);
    if (metric === 'avg_evapotranspiration') return Number(station.avg_evapotranspiration ?? 0);
    return Number(station.record_count ?? 0);
  }
  async function fetchStations() {
    const resp = await fetch(`${API_BASE}/bom/stations`);
    if (!resp.ok) throw new Error('Failed to load stations');
    return await resp.json();
  }

  // ----------------------------- core redraw -----------------------------
  async function redrawMarkersWithPalette(paletteName, palette) {
    try {
      const map = getMap();
      const layer = getMarkersLayer();
      if (!map || !layer) return; // map not ready yet

      const stations = await fetchStations();
      const metric = currentMetric();

      // Normalise values for palette mapping
      const vals = stations.map(s => valueForMetric(s, metric)).filter(Number.isFinite);
      const vmin = vals.length ? Math.min(...vals) : 0;
      const vmax = vals.length ? Math.max(...vals) : 1;
      const range = (vmax - vmin) || 1;

      const pal = palette && palette.length ? palette : getPaletteArray(paletteName || getSelectedPaletteName());

      // Clear any existing markers layer content
      try { layer.clearLayers(); } catch { /* ignore */ }

      // Add palette-coloured circle markers
      stations.forEach(station => {
        if (station.latitude && station.longitude) {
          const v = valueForMetric(station, metric);
          const t = (v - vmin) / range;
          const col = colourFromPalette(pal, t);

          const marker = L.circleMarker([station.latitude, station.longitude], {
            color: col, fillColor: col, fillOpacity: 0.9, radius: 7, weight: 1.5
          });

          const popupContent = `
            <div class="popup-station-name">${station.station_name ?? 'Station'}</div>
            <div><strong>Records:</strong> ${(station.record_count ?? 0).toLocaleString()}</div>
            <div><strong>State:</strong> ${station.state ?? 'N/A'}</div>
            <div><strong>Avg ET:</strong> ${
              (station.avg_evapotranspiration ?? null) !== null
                ? Number(station.avg_evapotranspiration).toFixed(2) + ' mm'
                : 'N/A'
            }</div>
          `;
          marker.bindPopup(popupContent);
          layer.addLayer(marker);
        }
      });
    } catch (e) {
      console.debug('a11y-markers redraw skipped:', e);
    }
  }

  // ----------------------------- public hooks -----------------------------
  // Called by a11y.js when the palette dropdown changes
  window.updateMarkersPalette = function (name, pal) { redrawMarkersWithPalette(name, pal); };

  // Also react when the metric selector changes or the Update map button is clicked
  document.addEventListener('change', function (e) {
    if (e.target && e.target.id === 'mapMetric') redrawMarkersWithPalette();
  });
  document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'updateMapBtn') {
      // Let any original update run first, then recolour
      setTimeout(() => redrawMarkersWithPalette(), 150);
    }
  });

  // ----------------------------- initialisation -----------------------------
  // Retry until the map and markers layer exist, then draw once
  function tryInitialDraw(attemptsLeft) {
    const map = getMap();
    const layer = getMarkersLayer();
    if (map && layer) {
      redrawMarkersWithPalette();
    } else if (attemptsLeft > 0) {
      setTimeout(() => tryInitialDraw(attemptsLeft - 1), 250);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    tryInitialDraw(20); // retry for ~5 seconds total
  });
})();
