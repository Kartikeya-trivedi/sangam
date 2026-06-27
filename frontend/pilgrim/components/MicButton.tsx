// Spec §2.1 / §2.9: one huge mic with a clear pulsing "listening" state.
export function MicButton({ recording, onPress }: { recording: boolean; onPress: () => void }) {
  return (
    <button className={`mic-button ${recording ? "recording" : ""}`} onClick={onPress}>
      <span className="mic-button__icon">🎤</span>
      <span>{recording ? "सुन रहे हैं… (Listening — tap to stop)" : "बोलिए / Speak"}</span>
    </button>
  );
}
