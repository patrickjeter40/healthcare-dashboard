import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import NoteAddOutlinedIcon from "@mui/icons-material/NoteAddOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import type { PatientNote } from "../api/types";
import { usePatientNotes } from "../hooks/usePatientNotes";
import { formatDateTime } from "../utils/format";

function localTimestamp(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16);
}

export function PatientNotesAndSummary({ patientId }: { patientId: string }) {
  const [draft, setDraft] = useState("");
  const [recordedAt, setRecordedAt] = useState(localTimestamp);
  const [timestampError, setTimestampError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [noteToDelete, setNoteToDelete] = useState<PatientNote | null>(null);
  const { notes, summary, addNote, removeNote, refresh } =
    usePatientNotes(patientId);

  async function submitNote(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setTimestampError("");
    const content = draft.trim();
    if (!content) {
      setError("Enter a note before adding it.");
      return;
    }
    if (content.length > 5000) {
      setError("Use 5,000 characters or fewer.");
      return;
    }
    const timestamp = new Date(recordedAt);
    if (!recordedAt || Number.isNaN(timestamp.getTime())) {
      setTimestampError("Enter a valid recorded date and time.");
      return;
    }
    if (timestamp.getTime() > Date.now()) {
      setTimestampError("Recorded date and time cannot be in the future.");
      return;
    }
    try {
      await addNote.mutateAsync({
        content,
        recorded_at: timestamp.toISOString(),
      });
      setDraft("");
      setRecordedAt(localTimestamp());
      await refresh();
      setNotice("Note added.");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not add the note.",
      );
    }
  }

  async function confirmDelete() {
    if (!noteToDelete) return;
    setError("");
    setNotice("");
    try {
      await removeNote.mutateAsync(noteToDelete.id);
      setNoteToDelete(null);
      await refresh();
      setNotice("Note removed from the active record.");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not remove the note.",
      );
      setNoteToDelete(null);
    }
  }

  return (
    <Box sx={{ display: "grid", gap: 2.5, mt: 2.5 }}>
      <Card>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 0.5 }}>
            Patient summary
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Generated from current patient information and recent notes.
          </Typography>
          {summary.isPending ? (
            <Stack spacing={1} aria-label="Loading summary">
              <Skeleton width="95%" />
              <Skeleton width="80%" />
              <Skeleton width="90%" />
            </Stack>
          ) : summary.isError ? (
            <Alert
              severity="error"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => summary.refetch()}
                >
                  Retry
                </Button>
              }
            >
              {summary.error.message}
            </Alert>
          ) : (
            <Typography
              variant="body2"
              sx={{
                whiteSpace: "pre-line",
                lineHeight: 1.8,
                overflowWrap: "anywhere",
              }}
            >
              {summary.data.summary}
            </Typography>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 0.5 }}>
            Clinical notes
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
            Recent notes appear first. Removed notes remain stored.
          </Typography>
          <Box component="form" noValidate onSubmit={submitNote} sx={{ mb: 3 }}>
            <TextField
              label="Recorded at"
              type="datetime-local"
              required
              value={recordedAt}
              onChange={(event) => {
                setRecordedAt(event.target.value);
                setTimestampError("");
              }}
              error={Boolean(timestampError)}
              helperText={
                timestampError ||
                "Enter your local time. Notes display in your local timezone."
              }
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
              size="small"
              sx={{ mb: 2 }}
            />
            <TextField
              label="Add a note"
              value={draft}
              onChange={(event) => {
                setDraft(event.target.value);
                if (error) setError("");
              }}
              multiline
              minRows={3}
              fullWidth
              slotProps={{ htmlInput: { maxLength: 5000 } }}
              helperText={`${draft.length}/5,000 characters`}
            />
            <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 1.5 }}>
              <Button
                type="submit"
                variant="contained"
                disabled={addNote.isPending}
                startIcon={
                  addNote.isPending ? (
                    <CircularProgress size={16} color="inherit" />
                  ) : (
                    <NoteAddOutlinedIcon />
                  )
                }
              >
                {addNote.isPending ? "Adding…" : "Add note"}
              </Button>
            </Box>
          </Box>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {notice && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {notice}
            </Alert>
          )}
          <Divider sx={{ mb: 2.5 }} />
          {notes.isPending ? (
            <Stack spacing={2} aria-label="Loading notes">
              <Skeleton variant="rounded" height={88} />
              <Skeleton variant="rounded" height={88} />
            </Stack>
          ) : notes.isError ? (
            <Alert
              severity="error"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => notes.refetch()}
                >
                  Retry
                </Button>
              }
            >
              {notes.error.message}
            </Alert>
          ) : notes.data.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No notes recorded yet.
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {notes.data.map((note) => (
                <Box
                  key={note.id}
                  sx={{
                    p: 2,
                    border: 1,
                    borderColor: "divider",
                    borderRadius: 2,
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 1,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {formatDateTime(note.recorded_at)}
                    </Typography>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<DeleteOutlineRoundedIcon />}
                      onClick={() => setNoteToDelete(note)}
                      aria-label={`Remove note from ${formatDateTime(note.recorded_at)}`}
                    >
                      Remove
                    </Button>
                  </Box>
                  <Typography
                    variant="body2"
                    sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
                  >
                    {note.content}
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={Boolean(noteToDelete)}
        onClose={() => !removeNote.isPending && setNoteToDelete(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Remove note?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This note will disappear from the active record and summary. It will
            remain stored.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            onClick={() => setNoteToDelete(null)}
            disabled={removeNote.isPending}
          >
            Cancel
          </Button>
          <Button
            color="error"
            variant="contained"
            onClick={confirmDelete}
            disabled={removeNote.isPending}
          >
            {removeNote.isPending ? "Removing…" : "Remove note"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
