import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { styled } from '@mui/material/styles';

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
}));

const NavBar = ({ onMenuClick }) => {
  return (
    <StyledAppBar position="fixed" color="default" elevation={1}>
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={onMenuClick}
          edge="start"
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
            BSLMap
          </Typography>
          <Typography variant="subtitle2" component="div" sx={{ ml: 2, color: 'text.secondary' }}>
            Global BSL-3/4 Laboratory Mapping
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
            Data last updated: {new Date().toLocaleDateString()}
          </Typography>
        </Box>
      </Toolbar>
    </StyledAppBar>
  );
};

export default NavBar;
