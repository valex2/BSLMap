import React, { useState, useEffect } from 'react';
import { Drawer, Box, Divider, List, ListItem, ListItemIcon, ListItemText, Typography, IconButton, TextField, InputAdornment, Collapse, Button, Chip, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';
import { ExpandLess, ExpandMore, Search, FilterList, Close } from '@mui/icons-material';
import { getPathogens, getResearchTypes } from '../services/api';

const drawerWidth = 300;

const StyledDrawer = styled(Drawer)(({ theme, open }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
  ...(open && {
    '& .MuiDrawer-paper': {
      width: drawerWidth,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
    },
  }),
  ...(!open && {
    '& .MuiDrawer-paper': {
      overflowX: 'hidden',
      width: 0,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
      }),
    },
  }),
}));

const Sidebar = ({ mobileOpen, onClose, isMobile }) => {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [pathogens, setPathogens] = useState([]);
  const [researchTypes, setResearchTypes] = useState([]);
  const [filters, setFilters] = useState({
    bslLevel: '',
    country: '',
    pathogen: '',
    researchType: ''
  });
  const [filterOpen, setFilterOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch filter options
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        setLoading(true);
        const [pathogensData, researchTypesData] = await Promise.all([
          getPathogens(),
          getResearchTypes()
        ]);
        setPathogens(pathogensData);
        setResearchTypes(researchTypesData);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching filter options:', err);
        setError('Failed to load filter options');
        setLoading(false);
      }
    };

    fetchFilterOptions();
  }, []);

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
    // TODO: Implement search functionality
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
    // TODO: Apply filters to the map
  };

  const clearFilters = () => {
    setFilters({
      bslLevel: '',
      country: '',
      pathogen: '',
      researchType: ''
    });
    // TODO: Clear all filters
  };

  const drawerContent = (
    <Box sx={{ overflow: 'auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            Filters
          </Typography>
          <IconButton onClick={onClose} size="small" sx={{ display: { xs: 'inline-flex', md: 'none' } }}>
            <Close />
          </IconButton>
        </Box>
        
        <TextField
          fullWidth
          variant="outlined"
          size="small"
          placeholder="Search labs..."
          value={searchQuery}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        
        <Box sx={{ mt: 2 }}>
          <Button
            fullWidth
            variant="outlined"
            size="small"
            startIcon={<FilterList />}
            endIcon={filterOpen ? <ExpandLess /> : <ExpandMore />}
            onClick={() => setFilterOpen(!filterOpen)}
            sx={{ justifyContent: 'space-between' }}
          >
            Advanced Filters
          </Button>
          
          <Collapse in={filterOpen} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                BSL Level
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {['BSL-2', 'BSL-3', 'BSL-4'].map((level) => (
                  <Chip
                    key={level}
                    label={level}
                    variant={filters.bslLevel === level ? 'filled' : 'outlined'}
                    color={filters.bslLevel === level ? 'primary' : 'default'}
                    onClick={() => handleFilterChange('bslLevel', filters.bslLevel === level ? '' : level)}
                    size="small"
                  />
                ))}
              </Box>
              
              <Typography variant="subtitle2" gutterBottom>
                Pathogens
              </Typography>
              {loading ? (
                <Typography variant="body2" color="text.secondary">
                  Loading pathogens...
                </Typography>
              ) : error ? (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              ) : (
                <Box sx={{ maxHeight: 150, overflowY: 'auto', mb: 2 }}>
                  {pathogens.slice(0, 10).map((pathogen) => (
                    <Chip
                      key={pathogen}
                      label={pathogen}
                      variant={filters.pathogen === pathogen ? 'filled' : 'outlined'}
                      color={filters.pathogen === pathogen ? 'primary' : 'default'}
                      onClick={() => handleFilterChange('pathogen', filters.pathogen === pathogen ? '' : pathogen)}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>
              )}
              
              <Typography variant="subtitle2" gutterBottom>
                Research Types
              </Typography>
              {loading ? (
                <Typography variant="body2" color="text.secondary">
                  Loading research types...
                </Typography>
              ) : error ? (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              ) : (
                <Box sx={{ maxHeight: 150, overflowY: 'auto', mb: 2 }}>
                  {researchTypes.slice(0, 10).map((type) => (
                    <Chip
                      key={type}
                      label={type}
                      variant={filters.researchType === type ? 'filled' : 'outlined'}
                      color={filters.researchType === type ? 'primary' : 'default'}
                      onClick={() => handleFilterChange('researchType', filters.researchType === type ? '' : type)}
                      size="small"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>
              )}
              
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={clearFilters}
                sx={{ mt: 1 }}
              >
                Clear All Filters
              </Button>
            </Box>
          </Collapse>
        </Box>
      </Box>
      
      <Box sx={{ p: 2, flexGrow: 1, overflowY: 'auto' }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Legend
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
          {[
            { level: 'BSL-4', color: '#F44336', description: 'Maximum Containment' },
            { level: 'BSL-3', color: '#FFC107', description: 'High Containment' },
            { level: 'BSL-2', color: '#4CAF50', description: 'Moderate Containment' },
            { level: 'Unknown', color: '#9E9E9E', description: 'Level Not Specified' },
          ].map((item) => (
            <Box key={item.level} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: item.color }} />
              <Typography variant="body2">
                <strong>{item.level}:</strong> {item.description}
              </Typography>
            </Box>
          ))}
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="body2" color="text.secondary" paragraph>
          This map displays BSL-3 and BSL-4 laboratories worldwide. Use the filters above to explore the data.
        </Typography>
        
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
          Data Sources: PubMed, Europe PMC, and other public sources
        </Typography>
      </Box>
    </Box>
  );

  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    );
  }

  return (
    <StyledDrawer
      variant="permanent"
      open={true}
      sx={{
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          position: 'relative',
          height: '100vh',
          borderRight: 'none',
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
        },
      }}
    >
      {drawerContent}
    </StyledDrawer>
  );
};

export default Sidebar;
