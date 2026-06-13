"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { getProgress } from "@/lib/api";
import type { ProgressStep } from "@/lib/types";

const FALLBACK: ProgressStep[] = [
  { ts: 0, icon: "🎙", text: "Распознаю речь" },
  { ts: 0, icon: "🧠", text: "Анализирую ответы" },
  { ts: 0, icon: "📝", text: "Готовлю результат" },
];

export function ProgressPanel({
  sessionId,
  title,
}: {
  sessionId: string;
  title: string;
}) {
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [estimate, setEstimate] = useState(45000);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const p = await getProgress(sessionId);
        if (!alive) return;
        setSteps(p.steps);
        setElapsed(p.elapsed_ms);
        if (p.estimate_ms) setEstimate(p.estimate_ms);
      } catch {
        /* во время ожидания сеть может моргать — игнорируем */
      }
    };
    poll();
    const id = setInterval(poll, 600);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [sessionId]);

  const shown = steps.length ? steps : FALLBACK;
  const sec = Math.floor(elapsed / 1000);
  const estSec = Math.round(estimate / 1000);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-4 text-center">
      <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
      <h2 className="mt-6 text-xl font-semibold text-slate-800">{title}</h2>

      {/* Закон №2: известное время — оценка + счётчик */}
      <p className="mt-2 text-sm text-slate-500">
        Прошло {sec} с · обычно занимает ≈{estSec} с
      </p>

      {/* Закон №3: объяснённое время — реальные шаги агента */}
      <ul className="mt-4 w-full space-y-1 text-left text-sm text-slate-600">
        {shown.map((s, i) => (
          <li key={i} className="flex items-center gap-2">
            <span>{s.icon}</span>
            <span>{s.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
