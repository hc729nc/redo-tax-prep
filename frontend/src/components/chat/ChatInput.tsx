import { useState } from "react";
import type { FormEvent } from "react";

export function ChatInput({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ display: "flex", gap: "0.5rem", padding: "0.75rem", borderTop: "1px solid #e5e5e5" }}
    >
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder="Tell Synthia about your tax situation..."
        style={{
          flex: 1,
          padding: "0.6rem 0.8rem",
          borderRadius: "8px",
          border: "1px solid #ccc",
          fontSize: "0.92rem",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        style={{
          padding: "0.6rem 1.1rem",
          borderRadius: "8px",
          border: "none",
          background: disabled ? "#aac" : "#2563eb",
          color: "#fff",
          fontSize: "0.92rem",
          cursor: disabled ? "default" : "pointer",
        }}
      >
        Send
      </button>
    </form>
  );
}
