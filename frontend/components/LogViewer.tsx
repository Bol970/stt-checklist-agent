"use client";

import { useState } from "react";
import { getLog } from "@/lib/api";

export function LogViewer({ sessionId }: { sessionId: string }) {
  const [open, setOpen] = useState(false);
  const [log, setLog] = useState("");

  async function toggle() {
    if (!open && !log) {
      try {
        setLog(await getLog(sessionId));
      } catch {
        setLog("(не удалось загрузить лог)");
      }
    }
    setOpen((v) => !v);
  }

  return (
    <div className="mt-6">
      <button
        onClick={toggle}
        className="text-sm font-medium text-slate-500 underline hover:text-slate-700"
      >
        {open ? "Скрыть лог сессии" : "Показать лог сессии (что делал агент)"}
      </button>
      {open && (
        <pre className="mt-2 max-h-80 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
          {log || "(лог пуст)"}
        </pre>
      )}
    </div>
  );
}
