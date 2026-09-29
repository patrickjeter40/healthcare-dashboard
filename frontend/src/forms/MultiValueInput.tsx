import { Autocomplete, TextField } from "@mui/material";
import type { ReferenceOption } from "../api/types";

interface MultiValueInputProps {
  label: string;
  options: ReferenceOption[];
  value: string[];
  onChange: (value: string[]) => void;
  onBlur: () => void;
  inputRef: (instance: HTMLInputElement | null) => void;
  error?: string;
}

export function MultiValueInput({
  label,
  options,
  value,
  onChange,
  onBlur,
  inputRef,
  error,
}: MultiValueInputProps) {
  return (
    <Autocomplete
      multiple
      options={options}
      value={options.filter((option) => value.includes(option.id))}
      getOptionLabel={(option) => option.name}
      getOptionKey={(option) => option.id}
      isOptionEqualToValue={(option, selected) => option.id === selected.id}
      filterSelectedOptions
      onChange={(_event, selected) =>
        onChange(selected.map((option) => option.id))
      }
      onBlur={onBlur}
      renderInput={(params) => (
        <TextField
          {...params}
          inputRef={inputRef}
          label={label}
          size="small"
          error={Boolean(error)}
          helperText={error ?? "Select documented values from the catalog."}
        />
      )}
    />
  );
}
