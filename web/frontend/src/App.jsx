import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import theme from './theme';
import MapPage from './pages/MapPage';
import NavBar from './components/NavBar';
import Sidebar from './components/Sidebar';
import { useMediaQuery } from '@mui/material';

function App() {
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <NavBar onMenuClick={handleDrawerToggle} />
        <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          <Sidebar 
            mobileOpen={mobileOpen} 
            onClose={handleDrawerToggle} 
            isMobile={isMobile} 
          />
          <Box 
            component="main" 
            sx={{ 
              flexGrow: 1, 
              overflow: 'auto',
              marginLeft: isMobile ? 0 : '300px',
              transition: theme.transitions.create('margin', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.leavingScreen,
              }),
            }}
          >
            <Routes>
              <Route path="/" element={<MapPage />} />
              <Route path="/labs" element={<MapPage />} />
              <Route path="/labs/:id" element={<MapPage />} />
            </Routes>
          </Box>
        </Box>
      </Box>
      <ReactQueryDevtools initialIsOpen={false} />
    </ThemeProvider>
  );
}

export default App;
