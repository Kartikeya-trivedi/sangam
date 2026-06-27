import { useCallback, useRef, useState } from "react";

// Spec §2.1 / §10: voice-first capture via MediaRecorder. tap-to-toggle.
export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream);
    chunksRef.current = [];
    mr.ondataavailable = (e) => {
      if (e.data.size) chunksRef.current.push(e.data);
    };
    mr.start();
    mediaRef.current = mr;
    setRecording(true);
  }, []);

  const stop = useCallback(
    () =>
      new Promise<Blob>((resolve) => {
        const mr = mediaRef.current;
        if (!mr) return resolve(new Blob());
        mr.onstop = () => {
          mr.stream.getTracks().forEach((t) => t.stop());
          setRecording(false);
          resolve(new Blob(chunksRef.current, { type: "audio/webm" }));
        };
        mr.stop();
      }),
    [],
  );

  return { recording, start, stop };
}
