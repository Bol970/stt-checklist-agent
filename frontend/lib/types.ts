export interface Question {
  id: string;
  text: string;
}

export interface StartResponse {
  session_id: string;
  round: number;
  max_rounds: number;
  questions: Question[];
  is_complete: false;
}

export interface SubmitNextRound {
  round: number;
  max_rounds: number;
  questions: Question[];
  round_summary: string;
  is_complete: false;
}

export interface SubmitComplete {
  round: number;
  is_complete: true;
  round_summary: string;
  checklist_preview: string;
}

export type SubmitResponse = SubmitNextRound | SubmitComplete;

export interface ChecklistItem {
  category: string;
  item: string;
  status: "confirmed" | "needs_clarification" | "not_discussed";
  notes: string | null;
}

export interface ProgressStep {
  ts: number;
  icon: string;
  text: string;
}

export interface ProgressResponse {
  steps: ProgressStep[];
  elapsed_ms: number;
  estimate_ms: number;
}
