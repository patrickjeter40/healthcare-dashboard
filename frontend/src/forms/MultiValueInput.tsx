import AddRoundedIcon from "@mui/icons-material/AddRounded";
import {
  Box,
  Button,
  Chip,
  FormHelperText,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

interface MultiValueInputProps {
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  error?: string;
}

export function MultiValueInput({
  label,
  value,
  onChange,
  error,
}: MultiValueInputProps) {
  const [draft, setDraft] = useState("");
  const [entryError, setEntryError] = useState("");

  function add() {
    const candidates = draft
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    if (!candidates.length) return;
    if (candidates.some((item) => item.length > 120)) {
      setEntryError("Each item must be 120 characters or fewer.");
      return;
    }
    const existing = new Set(value.map((item) => item.toLocaleLowerCase()));
    if (
      candidates.some((item) => existing.has(item.toLocaleLowerCase())) ||
      new Set(candidates.map((item) => item.toLocaleLowerCase())).size !==
        candidates.length
    ) {
      setEntryError("This item has already been added.");
      return;
    }
    if (value.length + candidates.length > 30) {
      setEntryError("Use 30 items or fewer.");
      return;
    }
    onChange([...value, ...candidates]);
    setDraft("");
    setEntryError("");
  }

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {label}
      </Typography>
      <Box sx={{ display: "flex", gap: 1 }}>
        <TextField
          size="small"
          fullWidth
          aria-label={`Add ${label.toLowerCase()}`}
          placeholder={`Add ${label === "Allergies" ? "allergy" : "condition"}`}
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
            setEntryError("");
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              add();
            }
          }}
          onBlur={() => {
            if (draft.trim()) add();
          }}
          error={Boolean(error || entryError)}
        />
        <Button
          variant="outlined"
          startIcon={<AddRoundedIcon />}
          onClick={add}
          onMouseDown={(event) => event.preventDefault()}
          disabled={!draft.trim()}
        >
          Add
        </Button>
      </Box>
      <FormHelperText
        error={Boolean(error || entryError)}
        sx={{ mx: 0, mt: 0.75 }}
      >
        {entryError ||
          error ||
          "Press Enter or Add. Separate multiple items with commas."}
      </FormHelperText>
      {value.length > 0 && (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1.5 }}>
          {value.map((item) => (
            <Chip
              key={item}
              label={item}
              onDelete={() =>
                onChange(value.filter((current) => current !== item))
              }
              sx={{ bgcolor: "#EBF5F4", color: "#235C58" }}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
