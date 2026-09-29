import { Chip } from "@mui/material";
import type { PatientStatus } from "../api/types";

const styles: Record<
  PatientStatus,
  { label: string; color: string; background: string }
> = {
  active: { label: "Active", color: "#087366", background: "#DDF5ED" },
  inactive: { label: "Inactive", color: "#6B5A1D", background: "#FFF1C9" },
  discharged: { label: "Discharged", color: "#5D6672", background: "#E9EEF1" },
};

export function PatientStatusChip({ status }: { status: PatientStatus }) {
  const style = styles[status];
  return (
    <Chip
      label={style.label}
      size="small"
      sx={{
        bgcolor: style.background,
        color: style.color,
        fontWeight: 700,
        borderRadius: 1.5,
      }}
    />
  );
}
