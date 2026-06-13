"use client";

import { Download, RotateCcw, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { renderMarkdown } from "@/lib/markdown";
import { LogViewer } from "@/components/LogViewer";

export function Results({
  markdown,
  sessionId,
  onRestart,
}: {
  markdown: string;
  sessionId: string;
  onRestart: () => void;
}) {
  function download() {
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `checklist-${sessionId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-4 py-10">
      <div className="mb-6 flex flex-col items-center text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
          <CheckCircle2 className="h-8 w-8 text-emerald-600" />
        </div>
        <h1 className="mt-4 text-3xl font-bold text-slate-900">Чеклист готов!</h1>
        <p className="mt-2 text-slate-600">
          Сформирован на основе ваших голосовых ответов.
        </p>
      </div>

      <Card>
        <CardContent>
          <div className="thin-scroll max-h-[60vh] overflow-y-auto pr-2">
            {renderMarkdown(markdown)}
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
        <Button onClick={download} variant="success" size="lg">
          <Download className="h-5 w-5" /> Скачать .md
        </Button>
        <Button onClick={onRestart} variant="outline" size="lg">
          <RotateCcw className="h-5 w-5" /> Начать заново
        </Button>
      </div>

      <LogViewer sessionId={sessionId} />
    </div>
  );
}
