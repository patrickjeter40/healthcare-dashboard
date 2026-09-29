import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import LocalHospitalRoundedIcon from "@mui/icons-material/LocalHospitalRounded";
import MenuRoundedIcon from "@mui/icons-material/MenuRounded";
import PeopleAltRoundedIcon from "@mui/icons-material/PeopleAltRounded";
import {
  Alert,
  Box,
  Button,
  Chip,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Snackbar,
  Typography,
} from "@mui/material";
import { useState } from "react";
import {
  Link as RouterLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

const drawerWidth = 248;

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const notice = (location.state as { notice?: string } | null)?.notice;

  function closeNotice() {
    navigate(`${location.pathname}${location.search}`, {
      replace: true,
      state: null,
    });
  }

  const navigation = (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        bgcolor: "#163541",
        color: "#FFF",
      }}
    >
      <Box
        sx={{ display: "flex", alignItems: "center", gap: 1.5, px: 3, py: 3.2 }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: 2.5,
            display: "grid",
            placeItems: "center",
            bgcolor: "#21A798",
          }}
        >
          <LocalHospitalRoundedIcon fontSize="small" />
        </Box>
        <Box>
          <Typography
            variant="subtitle1"
            sx={{ fontWeight: 800, lineHeight: 1.15, letterSpacing: "-0.02em" }}
          >
            CareView
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: "#9DB9C0", letterSpacing: "0.05em" }}
          >
            PATIENT WORKSPACE
          </Typography>
        </Box>
      </Box>

      <Typography
        variant="overline"
        sx={{
          px: 3,
          mt: 2,
          mb: 0.5,
          color: "#88A9B1",
          fontWeight: 700,
          letterSpacing: "0.14em",
        }}
      >
        WORKSPACE
      </Typography>
      <List sx={{ px: 1.5 }}>
        {[
          {
            label: "Overview",
            path: "/",
            icon: <DashboardRoundedIcon fontSize="small" />,
          },
          {
            label: "Patients",
            path: "/patients",
            icon: <PeopleAltRoundedIcon fontSize="small" />,
          },
        ].map((item) => {
          const selected =
            item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith("/patients");
          return (
            <ListItemButton
              key={item.path}
              component={RouterLink}
              to={item.path}
              selected={selected}
              onClick={() => setMobileOpen(false)}
              sx={{
                mb: 0.5,
                borderRadius: 2,
                color: selected ? "#FFF" : "#B5CBD0",
                "&.Mui-selected": { bgcolor: "#285562" },
                "&.Mui-selected:hover": { bgcolor: "#2C606D" },
                "&:hover": { bgcolor: "#214653" },
              }}
            >
              <ListItemIcon
                sx={{ color: selected ? "#6EE1CD" : "#A7C2C9", minWidth: 40 }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontWeight: selected ? 700 : 500 }}>
                    {item.label}
                  </Typography>
                }
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { width: drawerWidth, border: 0 },
        }}
      >
        {navigation}
      </Drawer>
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", md: "block" },
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            border: 0,
          },
        }}
      >
        {navigation}
      </Drawer>
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        <Box
          component="header"
          sx={{
            height: 72,
            px: { xs: 2, sm: 3, lg: 5 },
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            bgcolor: "background.paper",
            borderBottom: "1px solid",
            borderColor: "divider",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <IconButton
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
              sx={{ display: { md: "none" } }}
            >
              <MenuRoundedIcon />
            </IconButton>
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 700, color: "text.primary" }}
            >
              Patient workspace
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Box
              component="nav"
              aria-label="Header navigation"
              sx={{ display: { xs: "none", md: "flex" }, gap: 1 }}
            >
              <Button
                component={RouterLink}
                to="/"
                color="inherit"
                aria-current={location.pathname === "/" ? "page" : undefined}
              >
                Overview
              </Button>
              <Button
                component={RouterLink}
                to="/patients"
                color="inherit"
                aria-current={
                  location.pathname.startsWith("/patients") ? "page" : undefined
                }
              >
                Patients
              </Button>
            </Box>
            <Chip
              label="Fictional data"
              size="small"
              sx={{ bgcolor: "#E7F5F1", color: "#176C63", fontWeight: 700 }}
            />
          </Box>
        </Box>
        <Box
          component="main"
          sx={{
            maxWidth: 1440,
            mx: "auto",
            px: { xs: 2, sm: 3, lg: 5 },
            py: { xs: 3, md: 4 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={4000}
        onClose={closeNotice}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={closeNotice}
          severity="success"
          variant="filled"
          sx={{ width: "100%" }}
        >
          {notice}
        </Alert>
      </Snackbar>
    </Box>
  );
}
