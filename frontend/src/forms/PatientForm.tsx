import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { ReactNode } from "react";
import { Controller, useForm } from "react-hook-form";
import type { Control } from "react-hook-form";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { ApiError, createPatient, updatePatient } from "../api/client";
import type { Patient } from "../api/types";
import { patientName } from "../utils/format";
import { useAllergens, useConditions } from "../hooks/useReferenceData";
import { MultiValueInput } from "./MultiValueInput";
import {
  patientFormDefaults,
  patientSchema,
  toPatientWrite,
} from "./patientSchema";
import type { PatientFormValues } from "./patientSchema";

type TextFieldName = Exclude<
  keyof PatientFormValues,
  "allergy_ids" | "condition_ids"
>;

function FormTextField({
  name,
  label,
  control,
  type,
  required,
  select,
  children,
}: {
  name: TextFieldName;
  label: string;
  control: Control<PatientFormValues>;
  type?: string;
  required?: boolean;
  select?: boolean;
  children?: ReactNode;
}) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => {
        const { ref, ...inputField } = field;
        return (
          <TextField
            {...inputField}
            inputRef={ref}
            label={label}
            type={type}
            required={required}
            select={select}
            fullWidth
            size="small"
            error={Boolean(fieldState.error)}
            helperText={fieldState.error?.message}
            slotProps={
              type === "date" || type === "datetime-local"
                ? { inputLabel: { shrink: true } }
                : undefined
            }
          >
            {children}
          </TextField>
        );
      }}
    />
  );
}

function FormSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardContent
        sx={{
          p: { xs: 2.5, md: 3 },
          "&:last-child": { pb: { xs: 2.5, md: 3 } },
        }}
      >
        <Typography variant="h6">{title}</Typography>
        {description && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.5, mb: 2.5 }}
          >
            {description}
          </Typography>
        )}
        {!description && <Box sx={{ mb: 2.5 }} />}
        {children}
      </CardContent>
    </Card>
  );
}

export function PatientForm({ patient }: { patient?: Patient }) {
  const allergens = useAllergens();
  const conditions = useConditions();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState("");
  const form = useForm<PatientFormValues>({
    resolver: zodResolver(patientSchema),
    defaultValues: patientFormDefaults(patient),
    mode: "onBlur",
  });
  const mutation = useMutation({
    mutationFn: (values: PatientFormValues) => {
      const payload = toPatientWrite(values, patient);
      return patient
        ? updatePatient(patient.id, payload)
        : createPatient(payload);
    },
  });

  async function submit(values: PatientFormValues) {
    setSubmitError("");
    if (
      !allergens.data ||
      !conditions.data ||
      allergens.isError ||
      conditions.isError
    ) {
      setSubmitError("Load the allergy and condition catalogs before saving.");
      return;
    }
    let invalid = false;
    for (const [field, options] of [
      ["allergy_ids", allergens.data],
      ["condition_ids", conditions.data],
    ] as const) {
      if (
        values[field].some((id) => !options.some((option) => option.id === id))
      ) {
        form.setError(field, {
          message: "Select values from the loaded catalog.",
        });
        invalid = true;
      }
    }
    if (invalid) return;
    try {
      const saved = await mutation.mutateAsync(values);
      queryClient.setQueryData(["patient", saved.id], saved);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patients"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] }),
        queryClient.invalidateQueries({
          queryKey: ["patient-summary", saved.id],
        }),
      ]);
      navigate(`/patients/${saved.id}`, {
        state: { notice: patient ? "Patient updated." : "Patient created." },
      });
    } catch (error) {
      if (error instanceof ApiError) {
        let mapped = 0;
        for (const issue of error.issues) {
          const field = issue.loc[1];
          if (typeof field === "string" && field in form.getValues()) {
            form.setError(field as keyof PatientFormValues, {
              type: "server",
              message: issue.msg,
            });
            mapped += 1;
          }
        }
        setSubmitError(
          mapped
            ? "Review the highlighted fields and try again."
            : error.message,
        );
      } else {
        setSubmitError("Something went wrong. Please try again.");
      }
    }
  }

  if (allergens.isError || conditions.isError) {
    return (
      <Alert
        severity="error"
        action={
          <Button
            color="inherit"
            onClick={() => {
              void allergens.refetch();
              void conditions.refetch();
            }}
          >
            Retry
          </Button>
        }
      >
        Cannot load allergy and condition catalogs. The form is unavailable
        until both catalogs load.{" "}
        {allergens.error?.message ?? conditions.error?.message}
      </Alert>
    );
  }
  if (allergens.isPending || conditions.isPending) {
    return (
      <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
        <CircularProgress size={24} />
        Loading allergy and condition catalogs...
      </Box>
    );
  }

  const cancelTo = patient ? `/patients/${patient.id}` : "/patients";

  return (
    <Box>
      <Button
        component={RouterLink}
        to={cancelTo}
        startIcon={<ArrowBackRoundedIcon />}
        sx={{ mb: 2.5 }}
      >
        Back
      </Button>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="overline"
          color="primary"
          sx={{ fontWeight: 800, letterSpacing: "0.13em" }}
        >
          PATIENT RECORD
        </Typography>
        <Typography variant="h4" sx={{ mt: 0.5 }}>
          {patient ? `Edit ${patientName(patient)}` : "Add patient"}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          Fields marked with * are required.
        </Typography>
      </Box>

      <Box
        component="form"
        noValidate
        onSubmit={form.handleSubmit(submit)}
        sx={{ display: "grid", gap: 2.5, maxWidth: 960 }}
      >
        <FormSection
          title="Personal information"
          description="Basic details used to identify the patient."
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "minmax(0, 1fr)",
                sm: "repeat(2, minmax(0, 1fr))",
              },
              gap: 2,
            }}
          >
            <FormTextField
              name="first_name"
              label="First name"
              control={form.control}
              required
            />
            <FormTextField
              name="last_name"
              label="Last name"
              control={form.control}
              required
            />
            <FormTextField
              name="date_of_birth"
              label="Date of birth"
              control={form.control}
              type="date"
              required
            />
            <FormTextField
              name="status"
              label="Status"
              control={form.control}
              select
              required
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
              <MenuItem value="discharged">Discharged</MenuItem>
            </FormTextField>
            <FormTextField
              name="blood_type"
              label="Blood type"
              control={form.control}
              select
            >
              <MenuItem value="">Not recorded</MenuItem>
              {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map(
                (type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ),
              )}
            </FormTextField>
            <FormTextField
              name="last_visit_at"
              label="Last visit"
              control={form.control}
              type="datetime-local"
            />
          </Box>
        </FormSection>

        <FormSection
          title="Contact information"
          description="Optional contact and mailing details."
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "minmax(0, 1fr)",
                sm: "repeat(2, minmax(0, 1fr))",
              },
              gap: 2,
            }}
          >
            <FormTextField
              name="email"
              label="Email"
              control={form.control}
              type="email"
            />
            <FormTextField
              name="phone"
              label="Phone"
              control={form.control}
              type="tel"
            />
            <Box sx={{ gridColumn: { sm: "1 / -1" } }}>
              <FormTextField
                name="address_line_1"
                label="Address line 1"
                control={form.control}
              />
            </Box>
            <Box sx={{ gridColumn: { sm: "1 / -1" } }}>
              <FormTextField
                name="address_line_2"
                label="Address line 2"
                control={form.control}
              />
            </Box>
            <FormTextField name="city" label="City" control={form.control} />
            <FormTextField name="state" label="State" control={form.control} />
            <FormTextField
              name="postal_code"
              label="Postal code"
              control={form.control}
            />
          </Box>
        </FormSection>

        <FormSection
          title="Clinical information"
          description="Select documented allergies and conditions from the reference catalogs."
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "minmax(0, 1fr)",
                md: "repeat(2, minmax(0, 1fr))",
              },
              gap: 3,
            }}
          >
            <Controller
              name="allergy_ids"
              control={form.control}
              render={({ field, fieldState }) => (
                <MultiValueInput
                  label="Allergies"
                  options={allergens.data}
                  onBlur={field.onBlur}
                  inputRef={field.ref}
                  value={field.value}
                  onChange={field.onChange}
                  error={fieldState.error?.message}
                />
              )}
            />
            <Controller
              name="condition_ids"
              control={form.control}
              render={({ field, fieldState }) => (
                <MultiValueInput
                  label="Conditions"
                  options={conditions.data}
                  onBlur={field.onBlur}
                  inputRef={field.ref}
                  value={field.value}
                  onChange={field.onChange}
                  error={fieldState.error?.message}
                />
              )}
            />
          </Box>
        </FormSection>

        {submitError && <Alert severity="error">{submitError}</Alert>}
        <Box
          sx={{ display: "flex", justifyContent: "flex-end", gap: 1.5, pb: 3 }}
        >
          <Button component={RouterLink} to={cancelTo} color="inherit">
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={mutation.isPending}
            startIcon={
              mutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <SaveRoundedIcon />
              )
            }
          >
            {mutation.isPending
              ? "Saving…"
              : patient
                ? "Save changes"
                : "Create patient"}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
