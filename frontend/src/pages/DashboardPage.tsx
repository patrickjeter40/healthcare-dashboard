import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import PeopleAltRoundedIcon from "@mui/icons-material/PeopleAltRounded";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Skeleton,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";
import { getPatients } from "../api/client";
import type { PatientListParams, PatientStatus } from "../api/types";
import { PatientStatusChip } from "../components/PatientStatusChip";
import { formatDate, patientName } from "../utils/format";

const baseParams: PatientListParams = {
  page: 1,
  pageSize: 5,
  search: "",
  status: "",
  sortBy: "last_visit_at",
  sortOrder: "desc",
};

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <Card>
      <CardContent sx={{ p: 2.75, "&:last-child": { pb: 2.75 } }}>
        <Box
          sx={{
            width: 38,
            height: 38,
            display: "grid",
            placeItems: "center",
            borderRadius: 2,
            bgcolor: tone,
            mb: 2,
          }}
        >
          <PeopleAltRoundedIcon fontSize="small" color="primary" />
        </Box>
        <Typography variant="h4" sx={{ mb: 0.25 }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const overview = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: async ({ signal }) => {
      const [recent, active, inactive, discharged] = await Promise.all([
        getPatients(baseParams, signal),
        getPatients(
          { ...baseParams, pageSize: 1, status: "active" as PatientStatus },
          signal,
        ),
        getPatients(
          { ...baseParams, pageSize: 1, status: "inactive" as PatientStatus },
          signal,
        ),
        getPatients(
          { ...baseParams, pageSize: 1, status: "discharged" as PatientStatus },
          signal,
        ),
      ]);
      return {
        recent,
        active: active.total,
        inactive: inactive.total,
        discharged: discharged.total,
      };
    },
    staleTime: 30_000,
  });

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="overline"
          color="primary"
          sx={{ fontWeight: 800, letterSpacing: "0.13em" }}
        >
          OVERVIEW
        </Typography>
        <Typography variant="h4" sx={{ mt: 0.5 }}>
          Your patient panel
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          A quick view of patient records and recent visits.
        </Typography>
      </Box>

      {overview.isError ? (
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => overview.refetch()}
            >
              Retry
            </Button>
          }
        >
          {overview.error.message}
        </Alert>
      ) : (
        <>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "repeat(2, minmax(0, 1fr))",
                lg: "repeat(4, minmax(0, 1fr))",
              },
              gap: 2,
              mb: 4,
            }}
          >
            {overview.isPending ? (
              Array.from({ length: 4 }, (_, index) => (
                <Skeleton key={index} variant="rounded" height={150} />
              ))
            ) : (
              <>
                <MetricCard
                  label="Total patients"
                  value={overview.data.recent.total}
                  tone="#E3F5F1"
                />
                <MetricCard
                  label="Active"
                  value={overview.data.active}
                  tone="#DDF5ED"
                />
                <MetricCard
                  label="Inactive"
                  value={overview.data.inactive}
                  tone="#FFF1C9"
                />
                <MetricCard
                  label="Discharged"
                  value={overview.data.discharged}
                  tone="#E9EEF1"
                />
              </>
            )}
          </Box>

          <Card>
            <CardContent
              sx={{
                p: { xs: 2.5, md: 3 },
                "&:last-child": { pb: { xs: 2.5, md: 3 } },
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 2,
                  mb: 2,
                }}
              >
                <Box>
                  <Typography variant="h6">Recent visits</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Patients with the latest recorded visits
                  </Typography>
                </Box>
                <Button
                  component={RouterLink}
                  to="/patients"
                  endIcon={<ArrowForwardRoundedIcon />}
                  sx={{ flexShrink: 0 }}
                >
                  All patients
                </Button>
              </Box>
              {overview.isPending ? (
                Array.from({ length: 4 }, (_, index) => (
                  <Skeleton key={index} height={63} />
                ))
              ) : overview.data.recent.items.length === 0 ? (
                <Typography
                  color="text.secondary"
                  sx={{ py: 4, textAlign: "center" }}
                >
                  No patient records yet.
                </Typography>
              ) : (
                overview.data.recent.items.map((patient, index) => (
                  <Box key={patient.id}>
                    {index > 0 && <Divider />}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 2,
                        py: 1.7,
                        minWidth: 0,
                      }}
                    >
                      <Avatar
                        sx={{
                          bgcolor: "#D9EDEB",
                          color: "#146C65",
                          fontWeight: 700,
                          width: 40,
                          height: 40,
                        }}
                      >
                        {patient.first_name[0]}
                        {patient.last_name[0]}
                      </Avatar>
                      <Box sx={{ minWidth: 0, flexGrow: 1 }}>
                        <Typography
                          component={RouterLink}
                          to={`/patients/${patient.id}`}
                          sx={{
                            color: "text.primary",
                            fontWeight: 700,
                            textDecoration: "none",
                            "&:hover": {
                              color: "primary.main",
                              textDecoration: "underline",
                            },
                          }}
                        >
                          {patientName(patient)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Last visit {formatDate(patient.last_visit_at)}
                        </Typography>
                      </Box>
                      <Box sx={{ display: { xs: "none", sm: "block" } }}>
                        <PatientStatusChip status={patient.status} />
                      </Box>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
}
