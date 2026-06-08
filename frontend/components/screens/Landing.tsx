"use client";

import { Mic, ListChecks, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function Landing({
  onStart,
  loading,
  error,
}: {
  onStart: () => void;
  loading: boolean;
  error: string | null;
}) {
  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-4 py-12">
      <div className="mb-6 flex items-center gap-2 rounded-full bg-white/70 px-4 py-1.5 text-sm font-medium text-indigo-600 shadow-sm">
        <Sparkles className="h-4 w-4" /> Голосовой AI-агент
      </div>

      <h1 className="text-center text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
        Чеклист созвона с клиентом
      </h1>
      <p className="mt-4 max-w-xl text-center text-lg text-slate-600">
        Агент задаёт вопросы, вы отвечаете <strong>голосом</strong>. Whisper
        распознаёт речь, а модель анализирует ответы и формирует чеклист.
      </p>

      <Card className="mt-8 w-full">
        <CardContent className="flex flex-col gap-4">
          <Feature
            icon={<ListChecks className="h-5 w-5 text-indigo-600" />}
            title="3 раунда по 3 вопроса"
            text="Вопросы адаптируются под ваши предыдущие ответы."
          />
          <Feature
            icon={<Mic className="h-5 w-5 text-indigo-600" />}
            title="Отвечайте голосом"
            text="Нажмите «Записать», говорите — текст распознаётся автоматически."
          />
          <Feature
            icon={<Sparkles className="h-5 w-5 text-indigo-600" />}
            title="Готовый чеклист"
            text="В конце — структурированный чеклист с возможностью скачать .md"
          />
        </CardContent>
      </Card>

      <Button
        onClick={onStart}
        disabled={loading}
        size="lg"
        className="mt-8 w-full sm:w-auto"
      >
        {loading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" /> Запускаем…
          </>
        ) : (
          <>
            <Mic className="h-5 w-5" /> Начать сессию
          </>
        )}
      </Button>

      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
    </div>
  );
}

function Feature({
  icon,
  title,
  text,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50">
        {icon}
      </div>
      <div>
        <p className="font-semibold text-slate-800">{title}</p>
        <p className="text-sm text-slate-600">{text}</p>
      </div>
    </div>
  );
}
