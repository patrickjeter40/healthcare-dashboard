import { z } from "zod";
import type { Patient, PatientWrite } from "../api/types";

const requiredName = z
  .string()
  .trim()
  .min(1, "This field is required")
  .max(100, "Use 100 characters or fewer");
const optionalText = (limit: number) =>
  z.string().trim().max(limit, `Use ${limit} characters or fewer`);

function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return (
    !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
  );
}

const clinicalTerms = z
  .array(z.uuid())
  .max(30, "Use 30 items or fewer")
  .refine(
    (values) => new Set(values).size === values.length,
    "Remove duplicate items",
  );

export const patientSchema = z.object({
  first_name: requiredName,
  last_name: requiredName,
  date_of_birth: z
    .string()
    .refine(validDate, "Enter a valid date")
    .refine(
      (value) =>
        !validDate(value) || value <= new Date().toISOString().slice(0, 10),
      "Date of birth cannot be in the future",
    ),
  email: optionalText(320).refine(
    (value) => !value || z.email().safeParse(value).success,
    "Enter a valid email address",
  ),
  phone: optionalText(40),
  address_line_1: optionalText(200),
  address_line_2: optionalText(200),
  city: optionalText(100),
  state: optionalText(100),
  postal_code: optionalText(20),
  blood_type: z.enum(["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
  status: z.enum(["active", "inactive", "discharged"]),
  last_visit_at: z
    .string()
    .refine(
      (value) => !value || !Number.isNaN(new Date(value).getTime()),
      "Enter a valid visit date and time",
    )
    .refine(
      (value) =>
        !value ||
        Number.isNaN(new Date(value).getTime()) ||
        new Date(value) <= new Date(),
      "Last visit cannot be in the future",
    ),
  allergy_ids: clinicalTerms,
  condition_ids: clinicalTerms,
});

export type PatientFormValues = z.infer<typeof patientSchema>;

export function patientFormDefaults(patient?: Patient): PatientFormValues {
  let lastVisit = "";
  if (patient?.last_visit_at) {
    const date = new Date(patient.last_visit_at);
    lastVisit = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
      .toISOString()
      .slice(0, 16);
  }
  return {
    first_name: patient?.first_name ?? "",
    last_name: patient?.last_name ?? "",
    date_of_birth: patient?.date_of_birth ?? "",
    email: patient?.email ?? "",
    phone: patient?.phone ?? "",
    address_line_1: patient?.address_line_1 ?? "",
    address_line_2: patient?.address_line_2 ?? "",
    city: patient?.city ?? "",
    state: patient?.state ?? "",
    postal_code: patient?.postal_code ?? "",
    blood_type: patient?.blood_type ?? "",
    status: patient?.status ?? "active",
    last_visit_at: lastVisit,
    allergy_ids: patient?.allergies.map((item) => item.id) ?? [],
    condition_ids: patient?.conditions.map((item) => item.id) ?? [],
  };
}

export function toPatientWrite(values: PatientFormValues): PatientWrite {
  const optional = (value: string): string | null => value || null;
  return {
    first_name: values.first_name,
    last_name: values.last_name,
    date_of_birth: values.date_of_birth,
    email: optional(values.email),
    phone: optional(values.phone),
    address_line_1: optional(values.address_line_1),
    address_line_2: optional(values.address_line_2),
    city: optional(values.city),
    state: optional(values.state),
    postal_code: optional(values.postal_code),
    blood_type: values.blood_type || null,
    status: values.status,
    last_visit_at: values.last_visit_at
      ? new Date(values.last_visit_at).toISOString()
      : null,
    allergy_ids: values.allergy_ids,
    condition_ids: values.condition_ids,
  };
}
