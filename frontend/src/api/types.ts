export type PatientStatus = "active" | "inactive" | "discharged";
export type BloodType = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-";
export type PatientSortBy =
  "name" | "date_of_birth" | "last_visit_at" | "created_at" | "status";
export type SortOrder = "asc" | "desc";

export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  age: number;
  email: string | null;
  phone: string | null;
  address_line_1: string | null;
  address_line_2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  blood_type: BloodType | null;
  status: PatientStatus;
  last_visit_at: string | null;
  created_at: string;
  updated_at: string;
  allergies: string[];
  conditions: string[];
}

export interface PatientPage {
  items: Patient[];
  page: number;
  page_size: number;
  total: number;
}

export type PatientWrite = Omit<
  Patient,
  "id" | "age" | "created_at" | "updated_at"
>;

export interface PatientListParams {
  page: number;
  pageSize: number;
  search: string;
  status: PatientStatus | "";
  sortBy: PatientSortBy;
  sortOrder: SortOrder;
}

export interface PatientNote {
  id: string;
  patient_id: string;
  content: string;
  recorded_at: string;
  created_at: string;
}

export interface PatientSummary {
  patient_id: string;
  summary: string;
}
