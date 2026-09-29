import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addPatientNote,
  deletePatientNote,
  getPatientNotes,
  getPatientSummary,
} from "../api/client";
import type { NoteWrite } from "../api/types";

export function usePatientNotes(patientId: string) {
  const queryClient = useQueryClient();
  const notes = useQuery({
    queryKey: ["patient-notes", patientId],
    queryFn: ({ signal }) => getPatientNotes(patientId, signal),
  });
  const summary = useQuery({
    queryKey: ["patient-summary", patientId],
    queryFn: ({ signal }) => getPatientSummary(patientId, signal),
  });
  const addNote = useMutation({
    mutationFn: (data: NoteWrite) => addPatientNote(patientId, data),
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

  return { notes, summary, addNote, removeNote, refresh };
}
