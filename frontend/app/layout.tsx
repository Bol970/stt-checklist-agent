import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "STT Checklist Agent — голосовой агент",
  description:
    "Голосовой AI-агент: задаёт вопросы, слушает голосовые ответы (Whisper) и собирает чеклист созвона.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
