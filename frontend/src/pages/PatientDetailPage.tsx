import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import BloodtypeOutlinedIcon from "@mui/icons-material/BloodtypeOutlined";
import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import PhoneOutlinedIcon from "@mui/icons-material/PhoneOutlined";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Link,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import { ApiError, deletePatient, getPatient } from "../api/client";
import type { ReferenceOption } from "../api/types";
import { PatientStatusChip } from "../components/PatientStatusChip";
import { PatientNotesAndSummary } from "../components/PatientNotesAndSummary";
import { formatDate, patientName } from "../utils/format";

function InfoRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <Box
      sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, minWidth: 0 }}
    >
      <Box sx={{ color: "primary.main", mt: 0.25 }}>{icon}</Box>
      <Box sx={{ minWidth: 0 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "block", mb: 0.25 }}
        >
          {label}
        </Typography>
        <Typography
          variant="body2"
          sx={{ fontWeight: 600, overflowWrap: "anywhere" }}
        >
          {value || "Not recorded"}
        </Typography>
      </Box>
    </Box>
  );
}

function ClinicalList({
  title,
  terms,
  emptyMessage,
}: {
  title: string;
  terms: ReferenceOption[];
  emptyMessage: string;
}) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          {title}
        </Typography>
        {terms.length ? (
          <Stack
            direction="row"
            useFlexGap
            spacing={1}
            sx={{ flexWrap: "wrap" }}
          >
            {terms.map((term) => (
              <Chip
                key={term.id}
                label={term.name}
                sx={{ bgcolor: "#EBF5F4", color: "#235C58", fontWeight: 600 }}
              />
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            {emptyMessage}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export function PatientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const patient = useQuery({
    queryKey: ["patient", id],
    queryFn: ({ signal }) => getPatient(id ?? "", signal),
    enabled: Boolean(id),
    staleTime: 30_000,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && [404, 422].includes(error.status)) &&
      failureCount < 1,
  });
  const removePatient = useMutation({
    mutationFn: () => deletePatient(id ?? ""),
  });

  async function confirmDelete() {
    setDeleteError("");
    try {
      await removePatient.mutateAsync();
      queryClient.removeQueries({ queryKey: ["patient", id] });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patients"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] }),
      ]);
      navigate("/patients", {
        state: { notice: "Patient removed from active records." },
      });
    } catch (error) {
      setDeleteError(
        error instanceof Error
          ? error.message
          : "Could not remove this patient. Try again.",
      );
    }
  }

  if (patient.isPending) {
    return (
      <Stack spacing={2} aria-label="Loading patient">
        <Skeleton width={150} height={35} />
        <Skeleton width="55%" height={62} />
        <Skeleton variant="rounded" height={230} />
        <Skeleton variant="rounded" height={180} />
      </Stack>
    );
  }

  if (patient.isError) {
    const notFound =
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
          severity={notFound ? "warning" : "error"}
          action={
            !notFound ? (
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
          {notFound
            ? "This patient record is unavailable."
            : patient.error.message}
        </Alert>
      </Box>
    );
  }

  const record = patient.data;
  const address = [
    record.address_line_1,
    record.address_line_2,
    [record.city, record.state].filter(Boolean).join(", "),
    record.postal_code,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 1.5,
          mb: 2.5,
        }}
      >
        <Button
          component={RouterLink}
          to="/patients"
          startIcon={<ArrowBackRoundedIcon />}
        >
          Back to patients
        </Button>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            component={RouterLink}
            to={`/patients/${record.id}/edit`}
            variant="outlined"
            startIcon={<EditRoundedIcon />}
          >
            Edit
          </Button>
          <Button
            color="error"
            variant="outlined"
            startIcon={<DeleteOutlineRoundedIcon />}
            onClick={() => setConfirmOpen(true)}
          >
            Delete
          </Button>
        </Box>
      </Box>
      <Card sx={{ mb: 3, overflow: "hidden" }}>
        <Box sx={{ height: 7, bgcolor: "primary.main" }} />
        <CardContent
          sx={{
            p: { xs: 2.5, md: 3.5 },
            "&:last-child": { pb: { xs: 2.5, md: 3.5 } },
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: { xs: "flex-start", sm: "center" },
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Avatar
              sx={{
                bgcolor: "#DCEFEB",
                color: "#126E66",
                width: 64,
                height: 64,
                fontSize: 22,
                fontWeight: 700,
              }}
            >
              {record.first_name[0]}
              {record.last_name[0]}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography
                variant="overline"
                color="primary"
                sx={{ fontWeight: 800, letterSpacing: "0.12em" }}
              >
                PATIENT RECORD
              </Typography>
              <Typography variant="h4">{patientName(record)}</Typography>
              <Typography color="text.secondary">
                {record.age} years old · Born {formatDate(record.date_of_birth)}
              </Typography>
            </Box>
            <PatientStatusChip status={record.status} />
          </Box>
        </CardContent>
      </Card>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "minmax(0, 1fr)",
            lg: "minmax(0, 2fr) minmax(260px, 1fr)",
          },
          gap: 2.5,
          mb: 2.5,
        }}
      >
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2.5 }}>
              Patient information
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "minmax(0, 1fr)",
                  sm: "repeat(2, minmax(0, 1fr))",
                },
                gap: 3,
              }}
            >
              <InfoRow
                icon={<CalendarMonthOutlinedIcon fontSize="small" />}
                label="Date of birth"
                value={formatDate(record.date_of_birth)}
              />
              <InfoRow
                icon={<BloodtypeOutlinedIcon fontSize="small" />}
                label="Blood type"
                value={record.blood_type}
              />
              <InfoRow
                icon={<EmailOutlinedIcon fontSize="small" />}
                label="Email"
                value={
                  record.email ? (
                    <Link
                      href={`mailto:${record.email}`}
                      underline="always"
                      color="primary"
                    >
                      {record.email}
                    </Link>
                  ) : null
                }
              />
              <InfoRow
                icon={<PhoneOutlinedIcon fontSize="small" />}
                label="Phone"
                value={
                  record.phone ? (
                    <Link
                      href={`tel:${record.phone}`}
                      underline="always"
                      color="primary"
                    >
                      {record.phone}
                    </Link>
                  ) : null
                }
              />
            </Box>
            <Divider sx={{ my: 3 }} />
            <InfoRow
              icon={<HomeOutlinedIcon fontSize="small" />}
              label="Address"
              value={address}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2.5 }}>
              Visit details
            </Typography>
            <InfoRow
              icon={<CalendarMonthOutlinedIcon fontSize="small" />}
              label="Last visit"
              value={formatDate(record.last_visit_at)}
            />
            <Divider sx={{ my: 2.5 }} />
            <InfoRow
              icon={<CalendarMonthOutlinedIcon fontSize="small" />}
              label="Record created"
              value={formatDate(record.created_at)}
            />
          </CardContent>
        </Card>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "minmax(0, 1fr)",
            md: "repeat(2, minmax(0, 1fr))",
          },
          gap: 2.5,
        }}
      >
        <ClinicalList
          title="Allergies"
          terms={record.allergies}
          emptyMessage="No allergies documented."
        />
        <ClinicalList
          title="Conditions"
          terms={record.conditions}
          emptyMessage="No conditions documented."
        />
      </Box>
      <PatientNotesAndSummary key={record.id} patientId={record.id} />
      <Dialog
        open={confirmOpen}
        onClose={() => !removePatient.isPending && setConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Remove patient?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {patientName(record)} will no longer appear in the patient
            directory. Related clinical records will remain stored.
          </DialogContentText>
          {deleteError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {deleteError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            onClick={() => setConfirmOpen(false)}
            disabled={removePatient.isPending}
          >
            Cancel
          </Button>
          <Button
            color="error"
            variant="contained"
            onClick={confirmDelete}
            disabled={removePatient.isPending}
            startIcon={
              removePatient.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <DeleteOutlineRoundedIcon />
              )
            }
          >
            {removePatient.isPending ? "Removing…" : "Remove patient"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
