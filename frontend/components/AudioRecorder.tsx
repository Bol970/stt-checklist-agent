"use client";

import { useEffect } from "react";
import { Mic, Square, RotateCcw } from "lucide-react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { Button } from "@/components/ui/button";
import { formatSeconds } from "@/lib/utils";

export function AudioRecorder({
  onRecorded,
  disabled,
}: {
  onRecorded: (blob: Blob | null) => void;
  disabled?: boolean;
}) {
  const rec = useAudioRecorder(120);

  // Сообщаем родителю готовый blob.
  useEffect(() => {
    onRecorded(rec.blob);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rec.blob]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        {!rec.isRecording && !rec.blob && (
          <Button onClick={rec.start} disabled={disabled} variant="default" size="sm">
            <Mic className="h-4 w-4" /> Записать ответ
          </Button>
        )}

        {rec.isRecording && (
          <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75 animate-pulseRing" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-rose-500" />
            </span>
            <span className="font-mono text-sm text-rose-600">
              {formatSeconds(rec.seconds)}
            </span>
            <Button onClick={rec.stop} variant="danger" size="sm">
              <Square className="h-4 w-4" /> Стоп
            </Button>
          </div>
        )}

        {!rec.isRecording && rec.blob && (
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium text-emerald-600">
              ✅ Записано ({formatSeconds(rec.seconds)})
            </span>
            {rec.url && (
              <audio src={rec.url} controls className="h-9 max-w-[220px]" />
            )}
            <Button onClick={rec.reset} variant="ghost" size="sm" disabled={disabled}>
              <RotateCcw className="h-4 w-4" /> Перезаписать
            </Button>
          </div>
        )}
      </div>

      {rec.error && <p className="text-sm text-rose-600">{rec.error}</p>}
    </div>
  );
}
