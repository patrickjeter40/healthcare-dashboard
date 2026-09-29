import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import PersonAddAlt1RoundedIcon from "@mui/icons-material/PersonAddAlt1Rounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import SwapVertRoundedIcon from "@mui/icons-material/SwapVertRounded";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import { getPatients } from "../api/client";
import type {
  Patient,
  PatientSortBy,
  PatientStatus,
  SortOrder,
} from "../api/types";
import { PatientStatusChip } from "../components/PatientStatusChip";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatDate, patientName } from "../utils/format";

const sortOptions: { value: PatientSortBy; label: string }[] = [
  { value: "last_visit_at", label: "Last visit" },
  { value: "name", label: "Name" },
  { value: "status", label: "Status" },
  { value: "created_at", label: "Date added" },
];

function PatientAvatar({ patient }: { patient: Patient }) {
  return (
    <Avatar
      sx={{
        bgcolor: "#DCEFEB",
        color: "#126E66",
        fontWeight: 700,
        width: 38,
        height: 38,
        fontSize: 13,
      }}
    >
      {patient.first_name[0]}
      {patient.last_name[0]}
    </Avatar>
  );
}

export function PatientsPage() {
  const [searchInput, setSearchInput] = useState("");
  const search = useDebouncedValue(searchInput, 300);
  const [statusFilter, setStatusFilter] = useState<PatientStatus | "">("");
  const [sortBy, setSortBy] = useState<PatientSortBy>("last_visit_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const patients = useQuery({
    queryKey: [
      "patients",
      { page, pageSize, search, statusFilter, sortBy, sortOrder },
    ],
    queryFn: ({ signal }) =>
      getPatients(
        { page, pageSize, search, status: statusFilter, sortBy, sortOrder },
        signal,
      ),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });

  const hasFilters = Boolean(search || statusFilter);
  const items = patients.data?.items ?? [];

  return (
    <Box>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: { xs: "flex-start", sm: "center" },
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Typography
            variant="overline"
            color="primary"
            sx={{ fontWeight: 800, letterSpacing: "0.13em" }}
          >
            PATIENT DIRECTORY
          </Typography>
          <Typography variant="h4" sx={{ mt: 0.5 }}>
            Patients
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            Search records, review status, and open patient details.
          </Typography>
        </Box>
        <Button
          component={RouterLink}
          to="/patients/new"
          variant="contained"
          startIcon={<PersonAddAlt1RoundedIcon />}
        >
          Add patient
        </Button>
      </Box>

      <Card>
        <CardContent
          sx={{ p: { xs: 2, md: 3 }, "&:last-child": { pb: { xs: 2, md: 3 } } }}
        >
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 1.5,
              mb: 2.5,
            }}
          >
            <TextField
              label="Search patients"
              placeholder="Name or email"
              value={searchInput}
              onChange={(event) => {
                setSearchInput(event.target.value);
                setPage(1);
              }}
              size="small"
              sx={{ flex: "1 1 240px", minWidth: 0 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchRoundedIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <FormControl
              size="small"
              sx={{ minWidth: 145, flex: { xs: "1 1 140px", sm: "0 0 auto" } }}
            >
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                label="Status"
                inputProps={{ "aria-label": "Status" }}
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as PatientStatus | "");
                  setPage(1);
                }}
              >
                <MenuItem value="">All statuses</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="discharged">Discharged</MenuItem>
              </Select>
            </FormControl>
            <FormControl
              size="small"
              sx={{ minWidth: 150, flex: { xs: "1 1 140px", sm: "0 0 auto" } }}
            >
              <InputLabel id="sort-by-label">Sort by</InputLabel>
              <Select
                labelId="sort-by-label"
                label="Sort by"
                inputProps={{ "aria-label": "Sort by" }}
                value={sortBy}
                onChange={(event) => {
                  setSortBy(event.target.value as PatientSortBy);
                  setPage(1);
                }}
              >
                {sortOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Tooltip
              title={sortOrder === "asc" ? "Sort descending" : "Sort ascending"}
            >
              <IconButton
                aria-label={
                  sortOrder === "asc" ? "Sort descending" : "Sort ascending"
                }
                onClick={() => {
                  setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                  setPage(1);
                }}
                sx={{
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 2,
                }}
              >
                <SwapVertRoundedIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Box sx={{ minHeight: 25, mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {patients.isPending
                ? "Loading patients…"
                : patients.isError
                  ? "Unable to load patients"
                  : `${patients.data.total} ${patients.data.total === 1 ? "patient" : "patients"} found`}
            </Typography>
          </Box>

          {patients.isFetching && !patients.isPending && (
            <LinearProgress sx={{ mb: 1, borderRadius: 1 }} />
          )}

          {patients.isError ? (
            <Alert
              severity="error"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => patients.refetch()}
                >
                  Retry
                </Button>
              }
            >
              {patients.error.message}
            </Alert>
          ) : patients.isPending ? (
            <Stack spacing={1}>
              {Array.from({ length: 6 }, (_, index) => (
                <Skeleton key={index} variant="rounded" height={55} />
              ))}
            </Stack>
          ) : items.length === 0 ? (
            <Box sx={{ py: 7, textAlign: "center" }}>
              <PeopleAltOutlinedIcon
                sx={{ fontSize: 46, color: "#9CB2BA", mb: 1 }}
              />
              <Typography variant="h6">
                {hasFilters ? "No matching patients" : "No patients yet"}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                {hasFilters
                  ? "Try a different search or status filter."
                  : "Patient records will appear here."}
              </Typography>
              {hasFilters && (
                <Button
                  sx={{ mt: 2 }}
                  onClick={() => {
                    setSearchInput("");
                    setStatusFilter("");
                    setPage(1);
                  }}
                >
                  Clear filters
                </Button>
              )}
            </Box>
          ) : (
            <Box sx={{ opacity: patients.isPlaceholderData ? 0.55 : 1 }}>
              <TableContainer sx={{ display: { xs: "none", md: "block" } }}>
                <Table aria-label="Patients" size="medium">
                  <TableHead>
                    <TableRow sx={{ bgcolor: "#F7FAFB" }}>
                      {["Patient", "Age", "Last visit", "Status", ""].map(
                        (heading) => (
                          <TableCell
                            key={heading}
                            sx={{
                              fontWeight: 700,
                              color: "text.secondary",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {heading}
                          </TableCell>
                        ),
                      )}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((patient) => (
                      <TableRow key={patient.id} hover>
                        <TableCell>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1.5,
                              minWidth: 200,
                            }}
                          >
                            <PatientAvatar patient={patient} />
                            <Box sx={{ minWidth: 0 }}>
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
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ display: "block" }}
                              >
                                {patient.email || "No email"}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>{patient.age}</TableCell>
                        <TableCell sx={{ whiteSpace: "nowrap" }}>
                          {formatDate(patient.last_visit_at)}
                        </TableCell>
                        <TableCell>
                          <PatientStatusChip status={patient.status} />
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title={`Open ${patientName(patient)}`}>
                            <IconButton
                              component={RouterLink}
                              to={`/patients/${patient.id}`}
                              aria-label={`Open ${patientName(patient)}`}
                              size="small"
                            >
                              <ArrowForwardRoundedIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Stack spacing={1.5} sx={{ display: { xs: "flex", md: "none" } }}>
                {items.map((patient) => (
                  <Box
                    key={patient.id}
                    component={RouterLink}
                    to={`/patients/${patient.id}`}
                    sx={{
                      display: "block",
                      p: 2,
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 2,
                      color: "inherit",
                      textDecoration: "none",
                      "&:hover": {
                        borderColor: "primary.main",
                        bgcolor: "#F8FCFB",
                      },
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        gap: 1.5,
                        alignItems: "center",
                        mb: 1.5,
                      }}
                    >
                      <PatientAvatar patient={patient} />
                      <Box sx={{ minWidth: 0, flexGrow: 1 }}>
                        <Typography sx={{ fontWeight: 700 }}>
                          {patientName(patient)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Age {patient.age}
                        </Typography>
                      </Box>
                      <ArrowForwardRoundedIcon
                        fontSize="small"
                        color="action"
                      />
                    </Box>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 1,
                      }}
                    >
                      <Typography variant="body2" color="text.secondary">
                        Visit {formatDate(patient.last_visit_at)}
                      </Typography>
                      <PatientStatusChip status={patient.status} />
                    </Box>
                  </Box>
                ))}
              </Stack>

              <TablePagination
                component="div"
                count={patients.data.total}
                page={page - 1}
                onPageChange={(_, nextPage) => setPage(nextPage + 1)}
                rowsPerPage={pageSize}
                onRowsPerPageChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
                rowsPerPageOptions={[10, 20, 50]}
                sx={{
                  mt: 1,
                  borderTop: "1px solid",
                  borderColor: "divider",
                  "& .MuiTablePagination-toolbar": {
                    flexWrap: "wrap",
                    justifyContent: "center",
                  },
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
