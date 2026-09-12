import { useEffect, useRef } from "react";
import { MessageBubble, type ChatMessage } from "./MessageBubble";

export function ChatWindow({ messages }: { messages: ChatMessage[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {messages.length === 0 && (
        <p style={{ color: "#888", fontSize: "0.9rem" }}>
          Say hello to get started - tell Synthia a bit about your tax situation this
          year.
        </p>
      )}
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
