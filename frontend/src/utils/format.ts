export function patientName(patient: {
  first_name: string;
  last_name: string;
}): string {
  return `${patient.first_name} ${patient.last_name}`;
}

export function formatDate(value: string | null, timeZone?: string): string {
  if (!value) return "Not recorded";
  const date =
    value.length === 10 ? new Date(`${value}T12:00:00Z`) : new Date(value);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...(value.length === 10 || timeZone ? { timeZone: timeZone ?? "UTC" } : {}),
  }).format(date);
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(value));
}
