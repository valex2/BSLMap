import React, { useRef, useEffect, useState, useCallback } from 'react';
import maplibregl, { NavigationControl, ScaleControl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Box, Typography, CircularProgress } from '@mui/material';

// Debug logging
console.log('MapLibre GL initialized');

export const BSL_COLORS = {
  'BSL-2': '#4CAF50', // Green
  'BSL-3': '#FFC107', // Amber
  'BSL-4': '#F44336', // Red
  'Unknown': '#9E9E9E', // Grey
};

const MapComponent = ({ data, onLabSelect, selectedLabId }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (map.current) {
      console.log('Map already initialized');
      return;
    }
    
    if (!mapContainer.current) {
      console.error('Map container not found');
      return;
    }

    console.log('Initializing map with MapLibre GL version:', maplibregl.version);
    
    // Check if maplibregl is available
    if (!maplibregl) {
      console.error('maplibregl not found');
      return;
    }
    
    try {
      // Create a new map instance
      const mapInstance = new maplibregl.Map({
        container: mapContainer.current,
        style: 'https://demotiles.maplibre.org/style.json',
        center: [0, 20],
        zoom: 2,
        maxZoom: 18,
        minZoom: 1,
        maxBounds: [-180, -85, 180, 85],
        interactive: true,
        attributionControl: false
      });

      mapInstance.on('load', () => {
        console.log('Map loaded successfully');
        setMapLoaded(true);
      });

      mapInstance.on('error', (e) => {
        console.error('Map error:', e.error);
      });

      // Add controls
      mapInstance.addControl(new NavigationControl(), 'top-right');
      mapInstance.addControl(new ScaleControl());
      
      map.current = mapInstance;
      console.log('Map instance created');

      return () => {
        console.log('Cleaning up map...');
        if (map.current) {
          try {
            if (map.current.loaded()) {
              map.current.off();
              map.current.remove();
            }
          } catch (e) {
            console.error('Error during map cleanup:', e);
          } finally {
            map.current = null;
          }
        }
      };
    } catch (error) {
      console.error('Failed to initialize map:', error);
    }
  }, []);

  // Add data source and layers when map is loaded and data changes
  useEffect(() => {
    if (!map.current) {
      console.log('Map not initialized');
      return;
    }
    
    if (!mapLoaded) {
      console.log('Map not loaded yet');
      return;
    }
    
    if (!data) {
      console.log('No data available');
      return;
    }
    
    console.log('Processing data for map:', data);
    const sourceId = 'labs';
    const source = map.current.getSource(sourceId);

    if (source) {
      source.setData(data);
    } else {
      // Add the source and layers
      map.current.addSource(sourceId, {
        type: 'geojson',
        data,
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      // Add cluster circles
      map.current.addLayer({
        id: 'clusters',
        type: 'circle',
        source: sourceId,
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6',
            10,
            '#f1f075',
            30,
            '#f28cb1'
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            20,
            10,
            25,
            30,
            30
          ]
        }
      });

      // Add cluster count labels
      map.current.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: sourceId,
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 12
        }
      });

      // Add unclustered points
      map.current.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: sourceId,
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': [
            'match',
            ['get', 'bsl_level'],
            'BSL-2', BSL_COLORS['BSL-2'],
            'BSL-3', BSL_COLORS['BSL-3'],
            'BSL-4', BSL_COLORS['BSL-4'],
            BSL_COLORS['Unknown']
          ],
          'circle-radius': 8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.8
        }
      });

      // Add a layer for the selected point
      map.current.addLayer({
        id: 'selected-point',
        type: 'circle',
        source: sourceId,
        filter: ['==', 'id', ''], // Initially empty
        paint: {
          'circle-radius': 12,
          'circle-color': '#00f',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
          'circle-opacity': 1
        }
      });

      // Change the cursor to a pointer when the mouse is over a point
      map.current.on('mouseenter', 'unclustered-point', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      // Change it back to a pointer when it leaves
      map.current.on('mouseleave', 'unclustered-point', () => {
        map.current.getCanvas().style.cursor = '';
      });

      // Handle click on points
      map.current.on('click', 'unclustered-point', (e) => {
        const feature = e.features[0];
        onLabSelect(feature.properties);
      });

      // Handle click on clusters
      map.current.on('click', 'clusters', (e) => {
        const features = map.current.queryRenderedFeatures(e.point, {
          layers: ['clusters']
        });
        
        const clusterId = features[0].properties.cluster_id;
        const source = map.current.getSource(sourceId);
        
        source.getClusterExpansionZoom(
          clusterId,
          (err, zoom) => {
            if (err) return;
            
            map.current.easeTo({
              center: features[0].geometry.coordinates,
              zoom: zoom,
              duration: 500
            });
          }
        );
      });
    }

    // Update selected point filter when selectedLabId changes
    if (selectedLabId) {
      map.current.setFilter('selected-point', ['==', 'id', selectedLabId]);
    } else {
      map.current.setFilter('selected-point', ['==', 'id', '']);
    }

    // Cleanup
    return () => {
      if (map.current) {
        // Only remove layers and source if they exist
        if (map.current.getLayer('clusters')) {
          map.current.removeLayer('clusters');
        }
        if (map.current.getLayer('cluster-count')) {
          map.current.removeLayer('cluster-count');
        }
        if (map.current.getLayer('unclustered-point')) {
          map.current.removeLayer('unclustered-point');
        }
        if (map.current.getLayer('selected-point')) {
          map.current.removeLayer('selected-point');
        }
        if (map.current.getSource(sourceId)) {
          map.current.removeSource(sourceId);
        }
      }
    };
  }, [mapLoaded, data, selectedLabId, onLabSelect]);

  // Fit bounds when data changes
  useEffect(() => {
    if (!map.current || !mapLoaded || !data || !data.features || data.features.length === 0) return;

    if (data.features.length === 1 && selectedLabId) {
      // If we have a single selected lab, center on it
      const [lng, lat] = data.features[0].geometry.coordinates;
      map.current.flyTo({
        center: [lng, lat],
        zoom: 10,
        duration: 1000
      });
    } else if (data.features.length > 0) {
      // Otherwise, fit bounds to show all features
      const bounds = new maplibregl.LngLatBounds();
      data.features.forEach(feature => {
        bounds.extend(feature.geometry.coordinates);
      });
      
      // Add some padding
      const padding = {
        top: 50,
        bottom: 50,
        left: 50,
        right: 50
      };
      
      map.current.fitBounds(bounds, {
        padding: padding,
        duration: 1000
      });
    }
  }, [mapLoaded, data, selectedLabId]);

  return (
    <Box
      ref={mapContainer}
      sx={{
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: '#f0f0f0',
        '& .mapboxgl-canvas-container': {
          width: '100%',
          height: '100%',
        },
      }}
    >
      {!mapLoaded && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            zIndex: 1,
          }}
        >
          <CircularProgress />
          <Typography variant="body1" sx={{ mt: 2 }}>
            Loading map...
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default MapComponent;
