import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { Box, Button, Card, CardContent, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export function NotFoundPage() {
  return (
    <Card
      sx={{
        maxWidth: 600,
        mx: "auto",
        mt: { xs: 3, md: 8 },
        textAlign: "center",
      }}
    >
      <CardContent sx={{ p: { xs: 4, md: 7 } }}>
        <Typography
          variant="overline"
          color="primary"
          sx={{ fontWeight: 800, letterSpacing: "0.16em" }}
        >
          404 · PAGE NOT FOUND
        </Typography>
        <Typography variant="h4" sx={{ mt: 2, mb: 1 }}>
          This page is unavailable
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          The address may be incorrect, or the page may have moved.
        </Typography>
        <Box>
          <Button
            component={RouterLink}
            to="/patients"
            variant="contained"
            startIcon={<ArrowBackRoundedIcon />}
          >
            View patients
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
