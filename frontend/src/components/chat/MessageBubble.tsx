export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "0.75rem",
      }}
    >
      <div
        style={{
          maxWidth: "75%",
          padding: "0.6rem 0.9rem",
          borderRadius: "12px",
          background: isUser ? "#2563eb" : "#f1f3f5",
          color: isUser ? "#fff" : "#1a1a1a",
          whiteSpace: "pre-wrap",
          lineHeight: 1.45,
          fontSize: "0.92rem",
        }}
      >
        {message.text || (isUser ? "" : "…")}
      </div>
    </div>
  );
}
