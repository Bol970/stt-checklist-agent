"use client";

import { useState } from "react";
import { Landing } from "@/components/screens/Landing";
import { Interview } from "@/components/screens/Interview";
import { Results } from "@/components/screens/Results";
import { startSession } from "@/lib/api";
import type { Question, SubmitResponse } from "@/lib/types";

type Screen = "landing" | "interview" | "results";

interface SessionState {
  id: string;
  round: number;
  maxRounds: number;
  questions: Question[];
  roundSummary: string;
}

export default function Home() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);
  const [markdown, setMarkdown] = useState("");

  async function handleStart() {
    setError(null);
    setLoading(true);
    try {
      const res = await startSession();
      setSession({
        id: res.session_id,
        round: res.round,
        maxRounds: res.max_rounds,
        questions: res.questions,
        roundSummary: "",
      });
      setScreen("interview");
    } catch (e) {
      console.error(e);
      setError(
        "Не удалось начать сессию. Убедитесь, что бэкенд запущен и доступен по адресу из NEXT_PUBLIC_API_URL."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleResult(resp: SubmitResponse) {
    if (resp.is_complete) {
      setMarkdown(resp.checklist_preview);
      setScreen("results");
    } else if (session) {
      setSession({
        ...session,
        round: resp.round,
        questions: resp.questions,
        roundSummary: resp.round_summary,
      });
      // прокрутка вверх к новым вопросам
      if (typeof window !== "undefined") window.scrollTo({ top: 0 });
    }
  }

  function handleRestart() {
    setSession(null);
    setMarkdown("");
    setError(null);
    setScreen("landing");
  }

  if (screen === "landing") {
    return <Landing onStart={handleStart} loading={loading} error={error} />;
  }
  if (screen === "interview" && session) {
    return (
      <Interview
        sessionId={session.id}
        round={session.round}
        maxRounds={session.maxRounds}
        questions={session.questions}
        roundSummary={session.roundSummary}
        onResult={handleResult}
      />
    );
  }
  if (screen === "results" && session) {
    return (
      <Results
        markdown={markdown}
        sessionId={session.id}
        onRestart={handleRestart}
      />
    );
  }
  return null;
}
