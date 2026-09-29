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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  addPatientNote,
  deletePatientNote,
  getPatientNotes,
  getPatientSummary,
} from "../api/client";
import type { PatientNote } from "../api/types";
import { formatDate } from "../utils/format";

export function PatientNotesAndSummary({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [noteToDelete, setNoteToDelete] = useState<PatientNote | null>(null);
  const notes = useQuery({
    queryKey: ["patient-notes", patientId],
    queryFn: ({ signal }) => getPatientNotes(patientId, signal),
  });
  const summary = useQuery({
    queryKey: ["patient-summary", patientId],
    queryFn: ({ signal }) => getPatientSummary(patientId, signal),
  });
  const addNote = useMutation({
    mutationFn: (content: string) => addPatientNote(patientId, content),
  });
  const removeNote = useMutation({
    mutationFn: (noteId: string) => deletePatientNote(patientId, noteId),
  });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["patient-notes", patientId] }),
      queryClient.invalidateQueries({
        queryKey: ["patient-summary", patientId],
      }),
    ]);
  }

  async function submitNote(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const content = draft.trim();
    if (!content) {
      setError("Enter a note before adding it.");
      return;
    }
    if (content.length > 5000) {
      setError("Use 5,000 characters or fewer.");
      return;
    }
    try {
      await addNote.mutateAsync(content);
      setDraft("");
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
              sx={{ whiteSpace: "pre-line", lineHeight: 1.8 }}
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
            Recent notes appear first. Removed notes remain stored for audit
            purposes.
          </Typography>
          <Box component="form" onSubmit={submitNote} sx={{ mb: 3 }}>
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
                      {formatDate(note.recorded_at, "UTC")} UTC
                    </Typography>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<DeleteOutlineRoundedIcon />}
                      onClick={() => setNoteToDelete(note)}
                      aria-label={`Remove note from ${formatDate(note.recorded_at, "UTC")} UTC`}
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
            remain stored for audit purposes.
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
