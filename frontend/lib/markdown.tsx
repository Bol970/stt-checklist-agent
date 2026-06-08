import React from "react";

/** Мини-рендер markdown под формат, который генерит бэкенд
 * (заголовки, чекбоксы, цитаты, разделители, **bold**, `code`). */
export function renderMarkdown(md: string): React.ReactNode {
  const lines = md.split("\n");
  const out: React.ReactNode[] = [];

  lines.forEach((raw, i) => {
    const line = raw.replace(/\s+$/, "");
    const key = `l-${i}`;

    if (!line.trim()) {
      out.push(<div key={key} className="h-2" />);
      return;
    }
    if (line.startsWith("# ")) {
      out.push(
        <h1 key={key} className="mb-2 mt-1 text-2xl font-bold text-slate-900">
          {inline(line.slice(2))}
        </h1>
      );
      return;
    }
    if (line.startsWith("## ")) {
      out.push(
        <h2 key={key} className="mb-2 mt-5 border-b border-slate-100 pb-1 text-lg font-semibold text-slate-800">
          {inline(line.slice(3))}
        </h2>
      );
      return;
    }
    if (line.startsWith("- [x] ") || line.startsWith("- [ ] ")) {
      const checked = line.startsWith("- [x] ");
      out.push(
        <div key={key} className="flex items-start gap-2 py-0.5">
          <span
            className={
              "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-xs " +
              (checked
                ? "bg-emerald-500 text-white"
                : "border border-slate-300 bg-white text-transparent")
            }
          >
            ✓
          </span>
          <span className="text-sm text-slate-700">{inline(line.slice(6))}</span>
        </div>
      );
      return;
    }
    if (line.startsWith("> ") || line.startsWith("  > ")) {
      out.push(
        <p key={key} className="ml-7 border-l-2 border-slate-200 pl-3 text-sm italic text-slate-500">
          {inline(line.replace(/^\s*>\s?/, ""))}
        </p>
      );
      return;
    }
    if (line.startsWith("- ")) {
      out.push(
        <p key={key} className="text-sm font-medium text-slate-700">
          {inline(line.slice(2))}
        </p>
      );
      return;
    }
    if (line.startsWith("---")) {
      out.push(<hr key={key} className="my-3 border-slate-100" />);
      return;
    }
    out.push(
      <p key={key} className="text-sm text-slate-600">
        {inline(line)}
      </p>
    );
  });

  return <div>{out}</div>;
}

/** Обработка **bold**, *italic*, `code` внутри строки. */
function inline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let idx = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const token = m[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={idx++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      parts.push(
        <code key={idx++} className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-700">
          {token.slice(1, -1)}
        </code>
      );
    } else {
      parts.push(<em key={idx++}>{token.slice(1, -1)}</em>);
    }
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
