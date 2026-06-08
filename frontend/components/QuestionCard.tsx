"use client";

import { Card, CardContent } from "@/components/ui/card";
import { AudioRecorder } from "@/components/AudioRecorder";
import type { Question } from "@/lib/types";
import { cn } from "@/lib/utils";

export function QuestionCard({
  question,
  index,
  answered,
  onRecorded,
  disabled,
}: {
  question: Question;
  index: number;
  answered: boolean;
  onRecorded: (blob: Blob | null) => void;
  disabled?: boolean;
}) {
  return (
    <Card className={cn(answered && "ring-2 ring-emerald-200")}>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
              answered
                ? "bg-emerald-100 text-emerald-700"
                : "bg-indigo-100 text-indigo-700"
            )}
          >
            {index + 1}
          </div>
          <p className="pt-1 text-base font-medium leading-snug text-slate-800">
            {question.text}
          </p>
        </div>
        <AudioRecorder onRecorded={onRecorded} disabled={disabled} />
      </CardContent>
    </Card>
  );
}
