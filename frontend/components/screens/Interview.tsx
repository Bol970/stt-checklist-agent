"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";
import { ProgressPanel } from "@/components/ProgressPanel";
import { QuestionCard } from "@/components/QuestionCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { submitAnswers } from "@/lib/api";
import type { Question, SubmitResponse } from "@/lib/types";

export function Interview({
  sessionId,
  round,
  maxRounds,
  questions,
  roundSummary,
  onResult,
}: {
  sessionId: string;
  round: number;
  maxRounds: number;
  questions: Question[];
  roundSummary: string;
  onResult: (resp: SubmitResponse) => void;
}) {
  // blob по id вопроса
  const [blobs, setBlobs] = useState<Record<string, Blob | null>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answeredCount = useMemo(
    () => questions.filter((q) => blobs[q.id]).length,
    [questions, blobs]
  );
  const allAnswered = answeredCount === questions.length;

  async function handleSubmit(override?: Record<string, Blob>) {
    const src = override ?? blobs;
    setError(null);
    setSubmitting(true);
    try {
      const orderedBlobs = questions.map((q) => src[q.id] as Blob);
      const ids = questions.map((q) => q.id);
      const resp = await submitAnswers(sessionId, ids, orderedBlobs);
      onResult(resp);
    } catch (e) {
      console.error(e);
      setError(
        "Не удалось отправить ответы. Проверьте, что бэкенд запущен и доступен."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (submitting) {
    const last = round === maxRounds;
    return (
      <ProgressPanel
        sessionId={sessionId}
        title={last ? "Собираю чеклист…" : "Анализирую ваши ответы…"}
      />
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-10">
      {/* Прогресс раундов */}
      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-600">
          <span>
            Раунд {round} из {maxRounds}
          </span>
          <span>
            Отвечено {answeredCount}/{questions.length}
          </span>
        </div>
        <Progress value={((round - 1) / maxRounds) * 100} />
      </div>

      {answeredCount > 0 && (
        <p className="mb-4 text-center text-sm font-medium text-emerald-600">
          ✓ Ответ принят — можно переходить к следующему вопросу
        </p>
      )}

      {roundSummary && (
        <div className="mb-6 rounded-xl border border-indigo-100 bg-indigo-50/70 p-4 text-sm text-indigo-900">
          <span className="font-semibold">Контекст: </span>
          {roundSummary}
        </div>
      )}

      <div className="flex flex-col gap-4">
        {questions.map((q, i) => (
          <QuestionCard
            key={q.id}
            question={q}
            index={i}
            answered={!!blobs[q.id]}
            disabled={submitting}
            onRecorded={(blob) =>
              setBlobs((prev) => ({ ...prev, [q.id]: blob }))
            }
          />
        ))}
      </div>

      <div className="sticky bottom-4 mt-8">
        <Button
          onClick={() => handleSubmit()}
          disabled={!allAnswered || submitting}
          size="lg"
          className="w-full shadow-lg"
        >
          <Send className="h-5 w-5" />
          {round < maxRounds ? "Отправить ответы" : "Завершить и собрать чеклист"}
        </Button>
        {!allAnswered && (
          <p className="mt-2 text-center text-xs text-slate-500">
            Запишите ответ на каждый вопрос, чтобы продолжить.
          </p>
        )}
        {error && (
          <p className="mt-2 text-center text-sm text-rose-600">{error}</p>
        )}
        {process.env.NEXT_PUBLIC_DEMO_MODE === "true" && (
          <Button
            variant="outline"
            className="mt-2 w-full"
            disabled={submitting}
            onClick={() => {
              const filled: Record<string, Blob> = {};
              questions.forEach((q) => {
                filled[q.id] = new Blob([], { type: "audio/webm" });
              });
              setBlobs(filled);
              handleSubmit(filled); // передаём напрямую, не дожидаясь обновления state
            }}
          >
            ⚡ Демо: заполнить ответы автоматически
          </Button>
        )}
      </div>
    </div>
  );
}
