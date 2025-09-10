import React, { useState, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import Map from '../components/Map';
import LabDetails from '../components/LabDetails';
import { Box, CircularProgress, Typography, Paper } from '@mui/material';
import { getLabs, getLabById } from '../services/api';

const MapPage = () => {
  const { id: labId } = useParams();
  const [selectedLab, setSelectedLab] = useState(null);
  const [filters, setFilters] = useState({
    bslLevel: '',
    country: '',
    pathogen: '',
    researchType: ''
  });

  // Fetch all labs with filters
  const { data: labsData, isLoading, error } = useQuery(
    ['labs', filters], 
    () => getLabs(filters),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    }
  );

  // Fetch single lab when labId changes
  const { data: singleLab } = useQuery(
    ['lab', labId],
    () => getLabById(labId),
    {
      enabled: !!labId,
      onSuccess: (data) => {
        if (data) {
          setSelectedLab(data);
        }
      },
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    }
  );

  const handleLabSelect = useCallback((lab) => {
    setSelectedLab(lab);
  }, []);

  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }));
  }, []);

  // Combine the single lab with the labs data for the map
  const mapData = useMemo(() => {
    if (!labsData) return { type: 'FeatureCollection', features: [] };
    
    const features = [...labsData.features];
    
    // If we have a single lab that's not in the filtered results, add it
    if (singleLab && !features.some(f => f.id === singleLab.id)) {
      features.push(singleLab);
    }
    
    return {
      type: 'FeatureCollection',
      features
    };
  }, [labsData, singleLab]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">
          Error loading map data: {error.message}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <Map 
          data={mapData} 
          onLabSelect={handleLabSelect}
          selectedLabId={selectedLab?.id}
        />
        
        {/* Lab details panel */}
        {selectedLab && (
          <Paper 
            elevation={3} 
            sx={{
              position: 'absolute',
              top: 20,
              right: 20,
              width: 350,
              maxHeight: '80vh',
              overflowY: 'auto',
              zIndex: 1000,
            }}
          >
            <LabDetails 
              lab={selectedLab} 
              onClose={() => setSelectedLab(null)}
            />
          </Paper>
        )}
      </Box>
    </Box>
  );
};

export default MapPage;
