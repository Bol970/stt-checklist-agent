import type { StartResponse, SubmitResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:7860";

export function apiBase() {
  return API_BASE;
}

export async function startSession(): Promise<StartResponse> {
  const res = await fetch(`${API_BASE}/api/session/start`, { method: "POST" });
  if (!res.ok) throw new Error(`start failed: ${res.status}`);
  return res.json();
}

export async function submitAnswers(
  sessionId: string,
  questionIds: string[],
  blobs: Blob[]
): Promise<SubmitResponse> {
  const form = new FormData();
  blobs.forEach((b, i) => form.append("audio_files", b, `answer_${i}.webm`));
  form.append("question_ids", questionIds.join(","));

  const res = await fetch(`${API_BASE}/api/session/${sessionId}/submit`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`submit failed: ${res.status}`);
  return res.json();
}

/** Транскрипция одного аудио (превью перед подтверждением). */
export async function transcribeOne(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("audio_file", blob, "preview.webm");
  const res = await fetch(`${API_BASE}/api/session/transcribe`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`transcribe failed: ${res.status}`);
  const data = await res.json();
  return data.transcript as string;
}
