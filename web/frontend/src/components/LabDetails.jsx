import React from 'react';
import { 
  Box, 
  Typography, 
  Divider, 
  Chip, 
  IconButton, 
  Paper, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon,
  Link,
  Tooltip,
  useTheme
} from '@mui/material';
import { 
  Close as CloseIcon, 
  LocationOn as LocationIcon, 
  Science as ScienceIcon, 
  Article as ArticleIcon,
  Public as PublicIcon,
  Link as LinkIcon,
  Info as InfoIcon
} from '@mui/icons-material';

export const BSLBadge = ({ level }) => {
  const theme = useTheme();
  
  const getBSLColor = (level) => {
    switch(level) {
      case 'BSL-4':
        return theme.palette.error.main;
      case 'BSL-3':
        return theme.palette.warning.main;
      case 'BSL-2':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  return (
    <Chip 
      label={level || 'BSL Level Unknown'} 
      size="small"
      sx={{
        backgroundColor: getBSLColor(level),
        color: theme.palette.getContrastText(getBSLColor(level)),
        fontWeight: 'bold',
        px: 1,
      }}
    />
  );
};

const LabDetails = ({ lab, onClose }) => {
  const theme = useTheme();
  
  if (!lab) return null;

  const { 
    name, 
    institution, 
    address, 
    city, 
    country, 
    bsl_level, 
    pathogens = [], 
    research_types = [], 
    publications = [],
    website,
    coordinates
  } = lab.properties || lab;

  const formattedAddress = [address, city, country]
    .filter(Boolean)
    .join(', ');

  const handleViewOnMap = () => {
    // TODO: Implement map navigation to the lab
    console.log('View on map:', coordinates);
  };

  return (
    <Paper elevation={3} sx={{ p: 2, height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Box>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 600, mb: 0.5 }}>
            {name || institution || 'Unnamed Laboratory'}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <BSLBadge level={bsl_level} />
            {institution && institution !== name && (
              <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                {institution}
              </Typography>
            )}
          </Box>
        </Box>
        <IconButton size="small" onClick={onClose} aria-label="Close">
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
      
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <LocationIcon fontSize="small" color="action" sx={{ mr: 1 }} />
          <Typography variant="body2" color="text.secondary">
            {formattedAddress || 'Address not available'}
          </Typography>
        </Box>
        
        {website && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <LinkIcon fontSize="small" color="action" sx={{ mr: 1 }} />
            <Link 
              href={website.startsWith('http') ? website : `https://${website}`} 
              target="_blank" 
              rel="noopener noreferrer"
              variant="body2"
              sx={{ wordBreak: 'break-all' }}
            >
              {website.replace(/^https?:\/\//, '')}
            </Link>
          </Box>
        )}
        
        <Button 
          variant="outlined" 
          size="small" 
          startIcon={<PublicIcon />}
          onClick={handleViewOnMap}
          sx={{ mt: 1 }}
          fullWidth
        >
          View on Map
        </Button>
      </Box>
      
      <Divider sx={{ my: 1 }} />
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <ScienceIcon fontSize="small" sx={{ mr: 0.5 }} /> Research Focus
        </Typography>
        
        {research_types && research_types.length > 0 ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {research_types.map((type, index) => (
              <Chip 
                key={index} 
                label={type} 
                size="small" 
                variant="outlined"
                color="primary"
              />
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No research type information available
          </Typography>
        )}
        
        <Typography variant="subtitle2" gutterBottom sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
          <InfoIcon fontSize="small" sx={{ mr: 0.5 }} /> Pathogens Studied
        </Typography>
        
        {pathogens && pathogens.length > 0 ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {pathogens.map((pathogen, index) => (
              <Chip 
                key={index} 
                label={pathogen} 
                size="small" 
                variant="outlined"
                color="secondary"
              />
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No pathogen information available
          </Typography>
        )}
      </Box>
      
      <Divider sx={{ my: 1 }} />
      
      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <ArticleIcon fontSize="small" sx={{ mr: 0.5 }} /> Related Publications
        </Typography>
        
        {publications && publications.length > 0 ? (
          <List dense sx={{ overflowY: 'auto', flexGrow: 1, py: 0 }}>
            {publications.slice(0, 5).map((pub, index) => (
              <ListItem key={index} disableGutters sx={{ py: 0.5, px: 0 }}>
                <ListItemIcon sx={{ minWidth: 24, mr: 1 }}>
                  <ArticleIcon fontSize="small" color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Link 
                      href={`https://pubmed.ncbi.nlm.nih.gov/${pub.pmid}/`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      variant="body2"
                      color="primary"
                      sx={{ display: 'block' }}
                    >
                      {pub.title || `Publication ${index + 1}`}
                    </Link>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {pub.authors?.[0]?.name || 'Unknown author'}{pub.authors?.length > 1 ? ' et al.' : ''} • {pub.year || 'Year unknown'}
                    </Typography>
                  }
                  secondaryTypographyProps={{ component: 'div' }}
                  sx={{ my: 0 }}
                />
              </ListItem>
            ))}
            {publications.length > 5 && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 1 }}>
                + {publications.length - 5} more publications
              </Typography>
            )}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No publication information available
          </Typography>
        )}
      </Box>
      
      <Box sx={{ mt: 'auto', pt: 1 }}>
        <Divider sx={{ mb: 1 }} />
        <Typography variant="caption" color="text.secondary">
          Data last updated: {new Date().toLocaleDateString()}
        </Typography>
      </Box>
    </Paper>
  );
};

export default LabDetails;
