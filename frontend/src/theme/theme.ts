import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#087D76", dark: "#075F5B", light: "#E3F5F1" },
    secondary: { main: "#203B4B" },
    background: { default: "#F4F7F8", paper: "#FFFFFF" },
    text: { primary: "#18333F", secondary: "#627580" },
    divider: "#E1E9EC",
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily:
      'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h4: { fontWeight: 750, letterSpacing: "-0.035em" },
    h5: { fontWeight: 750, letterSpacing: "-0.025em" },
    h6: { fontWeight: 700 },
    button: { fontWeight: 700, textTransform: "none" },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { border: "1px solid #E1E9EC", boxShadow: "none" },
      },
    },
    MuiButton: { styleOverrides: { root: { borderRadius: 9 } } },
  },
});
