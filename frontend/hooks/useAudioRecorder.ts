"use client";

import { useCallback, useRef, useState } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  seconds: number;
  blob: Blob | null;
  url: string | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

/** Хук записи голоса через MediaRecorder. Отдаёт webm/opus Blob. */
export function useAudioRecorder(maxSeconds = 120): AudioRecorderState {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const cleanupStream = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    stopTimer();
    setIsRecording(false);
  }, []);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const finalBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        setBlob(finalBlob);
        setUrl(URL.createObjectURL(finalBlob));
        cleanupStream();
      };

      // сброс предыдущей записи
      setBlob(null);
      setUrl(null);
      setSeconds(0);

      recorder.start();
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setSeconds((s) => {
          if (s + 1 >= maxSeconds) stop();
          return s + 1;
        });
      }, 1000);
    } catch (e) {
      setError(
        "Не удалось получить доступ к микрофону. Разрешите доступ в браузере."
      );
      console.error(e);
    }
  }, [maxSeconds, stop]);

  const reset = useCallback(() => {
    stop();
    setBlob(null);
    if (url) URL.revokeObjectURL(url);
    setUrl(null);
    setSeconds(0);
    setError(null);
  }, [stop, url]);

  return { isRecording, seconds, blob, url, error, start, stop, reset };
}
