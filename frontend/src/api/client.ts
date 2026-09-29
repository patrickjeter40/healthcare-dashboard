import type {
  Patient,
  PatientListParams,
  PatientNote,
  PatientPage,
  PatientSummary,
  PatientWrite,
} from "./types";

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly issues: ValidationIssue[];

  constructor(message: string, status: number, issues: ValidationIssue[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.issues = issues;
  }
}

export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
}

type ErrorBody = { detail?: string | ValidationIssue[] };

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: options.method ?? "GET",
      headers:
        options.body === undefined
          ? undefined
          : { "Content-Type": "application/json" },
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new ApiError(
      "Cannot reach the server. Check your connection and try again.",
      0,
    );
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody;
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((issue) => issue.msg)
              .filter(Boolean)
              .join("; ")
          : "";
    throw new ApiError(
      message || `The request failed (${response.status}).`,
      response.status,
      Array.isArray(detail) ? detail : [],
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getPatients(
  params: PatientListParams,
  signal?: AbortSignal,
): Promise<PatientPage> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
    sort_by: params.sortBy,
    sort_order: params.sortOrder,
  });
  if (params.search.trim()) query.set("search", params.search.trim());
  if (params.status) query.set("status", params.status);
  return request<PatientPage>(`/patients?${query.toString()}`, { signal });
}

export function getPatient(id: string, signal?: AbortSignal): Promise<Patient> {
  return request<Patient>(`/patients/${encodeURIComponent(id)}`, { signal });
}

export function createPatient(data: PatientWrite): Promise<Patient> {
  return request<Patient>("/patients", { method: "POST", body: data });
}

export function updatePatient(
  id: string,
  data: PatientWrite,
): Promise<Patient> {
  return request<Patient>(`/patients/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: data,
  });
}

export function deletePatient(id: string): Promise<void> {
  return request<void>(`/patients/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function getPatientNotes(
  id: string,
  signal?: AbortSignal,
): Promise<PatientNote[]> {
  return request<PatientNote[]>(`/patients/${encodeURIComponent(id)}/notes`, {
    signal,
  });
}

export function addPatientNote(
  id: string,
  content: string,
): Promise<PatientNote> {
  return request<PatientNote>(`/patients/${encodeURIComponent(id)}/notes`, {
    method: "POST",
    body: { content },
  });
}

export function deletePatientNote(id: string, noteId: string): Promise<void> {
  return request<void>(
    `/patients/${encodeURIComponent(id)}/notes/${encodeURIComponent(noteId)}`,
    { method: "DELETE" },
  );
}

export function getPatientSummary(
  id: string,
  signal?: AbortSignal,
): Promise<PatientSummary> {
  return request<PatientSummary>(
    `/patients/${encodeURIComponent(id)}/summary`,
    { signal },
  );
}
