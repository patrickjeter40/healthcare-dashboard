import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import { Alert, Box, Button, Skeleton, Stack } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";
import { ApiError, getPatient } from "../api/client";
import { PatientForm } from "../forms/PatientForm";

export function CreatePatientPage() {
  return <PatientForm />;
}

export function EditPatientPage() {
  const { id } = useParams();
  const patient = useQuery({
    queryKey: ["patient", id],
    queryFn: ({ signal }) => getPatient(id ?? "", signal),
    enabled: Boolean(id),
    retry: (failureCount, error) =>
      !(error instanceof ApiError && [404, 422].includes(error.status)) &&
      failureCount < 1,
  });

  if (patient.isPending) {
    return (
      <Stack spacing={2} aria-label="Loading patient form">
        <Skeleton width={180} height={45} />
        <Skeleton variant="rounded" height={250} />
        <Skeleton variant="rounded" height={250} />
      </Stack>
    );
  }

  if (patient.isError) {
    const unavailable =
      patient.error instanceof ApiError &&
      [404, 422].includes(patient.error.status);
    return (
      <Box>
        <Button
          component={RouterLink}
          to="/patients"
          startIcon={<ArrowBackRoundedIcon />}
          sx={{ mb: 3 }}
        >
          Back to patients
        </Button>
        <Alert
          severity={unavailable ? "warning" : "error"}
          action={
            !unavailable ? (
              <Button
                color="inherit"
                size="small"
                onClick={() => patient.refetch()}
              >
                Retry
              </Button>
            ) : undefined
          }
        >
          {unavailable
            ? "This patient record is unavailable."
            : patient.error.message}
        </Alert>
      </Box>
    );
  }

  return <PatientForm key={patient.data.id} patient={patient.data} />;
}
