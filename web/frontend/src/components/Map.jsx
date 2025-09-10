import { useEffect, useRef, useState, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Box, Typography, CircularProgress } from '@mui/material';

const baseStyle = {
  version: 8,
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm-tiles', type: 'raster', source: 'osm-tiles' }],
};

const LAB_SOURCE_ID = 'labs';
const LAB_CIRCLE_LAYER_ID = 'labs-circle';
const LAB_LABEL_LAYER_ID = 'labs-labels';
const LAB_SELECTED_LAYER_ID = 'labs-selected-outline';

export default function MapComponent({ data, onLabSelect, selectedLabId }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [loaded, setLoaded] = useState(false);

  // Keep a stable, validated GeoJSON value (MapLibre dislikes changing object identities unnecessarily)
  const geojson = useMemo(() => {
    if (!data || data.type !== 'FeatureCollection') return { type: 'FeatureCollection', features: [] };
    return data;
  }, [data]);

  // INIT (once)
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: baseStyle,
      center: [0, 20],
      zoom: 1.8,
      attributionControl: false,
      cooperativeGestures: true,
    });

    mapRef.current = map;

    // Controls
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }));

    // Basic error surface (prevents silent failures = blue square)
    map.on('error', (e) => {
      // eslint-disable-next-line no-console
      console.error('[MapLibre error]', e?.error || e);
    });

    map.once('load', () => setLoaded(true));

    // Resize when container changes
    const ro = new ResizeObserver(() => {
      // Avoid spam; MapLibre handles most resize, but this helps inside flex layouts
      if (!map.isMoving()) {
        map.resize();
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // DATA (add once, then setData thereafter)
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const map = mapRef.current;

    // If source exists, just setData
    const existing = map.getSource(LAB_SOURCE_ID);
    if (existing) {
      try {
        existing.setData(geojson);
      } catch (e) {
        console.warn('[labs] setData failed; recreating source', e);
        if (map.getLayer(LAB_LABEL_LAYER_ID)) map.removeLayer(LAB_LABEL_LAYER_ID);
        if (map.getLayer(LAB_SELECTED_LAYER_ID)) map.removeLayer(LAB_SELECTED_LAYER_ID);
        if (map.getLayer(LAB_CIRCLE_LAYER_ID)) map.removeLayer(LAB_CIRCLE_LAYER_ID);
        if (map.getSource(LAB_SOURCE_ID)) map.removeSource(LAB_SOURCE_ID);
      }
    }

    // (Re)create source/layers if needed
    if (!map.getSource(LAB_SOURCE_ID)) {
      map.addSource(LAB_SOURCE_ID, {
        type: 'geojson',
        data: geojson,
        // If your features include a stable `id` (string/number) at top-level or in properties,
        // you can promote it for faster filters. If your id lives in properties.id, use:
        // promoteId: 'id', // (enable if your FEATURES have top-level "id")
      });

      map.addLayer({
        id: LAB_CIRCLE_LAYER_ID,
        type: 'circle',
        source: LAB_SOURCE_ID,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['to-number', ['get', 'evidence_count'], 1],
            1, 3,
            1000, 10,
          ],
          'circle-color': '#1f77b4',
          'circle-opacity': 0.75,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#ffffff',
        },
      });

      map.addLayer({
        id: LAB_LABEL_LAYER_ID,
        type: 'symbol',
        source: LAB_SOURCE_ID,
        layout: {
          'text-field': ['coalesce', ['get', 'institution'], ''],
          'text-size': 11,
          'text-offset': [0, 1.2],
          'text-anchor': 'top',
          'text-optional': true,
        },
        paint: {
          'text-color': '#0b132b',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1,
        },
      });

      // Selected outline layer (drawn atop)
      map.addLayer({
        id: LAB_SELECTED_LAYER_ID,
        type: 'circle',
        source: LAB_SOURCE_ID,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['to-number', ['get', 'evidence_count'], 1],
            1, 5,
            1000, 12,
          ],
          'circle-color': 'transparent',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ff6b00',
        },
        filter: ['==', ['get', 'id'], '__none__'], // will be updated below
      });
    } else {
      // If source already existed, ensure layers exist (in case of prior removal)
      if (!map.getLayer(LAB_CIRCLE_LAYER_ID) || !map.getLayer(LAB_LABEL_LAYER_ID)) {
        // Remove any remnants then re-add cleanly
        if (map.getLayer(LAB_LABEL_LAYER_ID)) map.removeLayer(LAB_LABEL_LAYER_ID);
        if (map.getLayer(LAB_SELECTED_LAYER_ID)) map.removeLayer(LAB_SELECTED_LAYER_ID);
        if (map.getLayer(LAB_CIRCLE_LAYER_ID)) map.removeLayer(LAB_CIRCLE_LAYER_ID);
        // Recurse once to rebuild layers
        map.removeSource(LAB_SOURCE_ID);
        // Trigger rebuild on next effect tick
        setTimeout(() => {
          if (mapRef.current) {
            mapRef.current.addSource(LAB_SOURCE_ID, { type: 'geojson', data: geojson });
            // Layers will be added on next render cycle
          }
        }, 0);
      }
    }

    // Click -> onLabSelect(feature)
    const handleClick = (e) => {
      const f = map.queryRenderedFeatures(e.point, { layers: [LAB_CIRCLE_LAYER_ID] })?.[0];
      if (f && typeof onLabSelect === 'function') onLabSelect(f);
    };
    map.on('click', handleClick);

    return () => {
      map.off('click', handleClick);
      // Note: we do NOT remove layers/sources here to avoid thrash; cleanup happens on unmount
    };
  }, [loaded, geojson, onLabSelect]);

  // Selected highlight filter
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.getLayer(LAB_SELECTED_LAYER_ID)) return;

    // Try matching by top-level feature id if present, else by properties.id, else by institution
    let filter = ['==', ['get', 'id'], '__none__'];
    if (selectedLabId != null) {
      filter = [
        'any',
        ['==', ['id'], selectedLabId],                 // top-level feature id
        ['==', ['get', 'id'], selectedLabId],          // properties.id
        ['==', ['get', 'institution'], selectedLabId], // fallback: institution string
      ];
    }
    map.setFilter(LAB_SELECTED_LAYER_ID, filter);
  }, [loaded, selectedLabId]);

  return (
    <Box
      ref={containerRef}
      sx={{
        width: '100%',
        height: '100%',
        minHeight: 500,
        position: 'relative',
        // Ensure the canvas actually fills its parent in flex/grid layouts
        '& .maplibregl-canvas': { width: '100% !important', height: '100% !important' },
      }}
    >
      {!loaded && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: 1,
            zIndex: 1,
            pointerEvents: 'none',
          }}
        >
          <CircularProgress />
          <Typography variant="body2">Loading map…</Typography>
        </Box>
      )}
    </Box>
  );
}