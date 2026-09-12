import { useEffect, useRef, useState } from "react";
import { chatApi } from "../api/chatApi";
import { documentsApi, type ExtractedField } from "../api/documentsApi";
import { ChatWindow } from "../components/chat/ChatWindow";
import { ChatInput } from "../components/chat/ChatInput";
import type { ChatMessage } from "../components/chat/MessageBubble";
import { UploadWidget } from "../components/documents/UploadWidget";
import { FieldConfirmationPanel } from "../components/documents/FieldConfirmationPanel";
import { ReturnSummary } from "../components/review/ReturnSummary";
import { PriorYearPanel } from "../components/priorYear/PriorYearPanel";

export function ChatPage({ taxReturnId }: { taxReturnId: string }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const nextId = useRef(0);

  useEffect(() => {
    chatApi.createSession(taxReturnId).then((s) => setSessionId(s.id));
    refreshFields();
  }, [taxReturnId]);

  async function refreshFields() {
    const f = await documentsApi.listFields(taxReturnId);
    setFields(f);
  }

  async function handleSend(text: string) {
    if (!sessionId) return;
    const userMessage: ChatMessage = { id: String(nextId.current++), role: "user", text };
    const assistantId = String(nextId.current++);
    setMessages((prev) => [...prev, userMessage, { id: assistantId, role: "assistant", text: "" }]);
    setSending(true);

    try {
      await chatApi.streamMessage(
        sessionId,
        text,
        (token) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, text: m.text + token } : m))
          );
        },
        () => {
          setSending(false);
          refreshFields();
        }
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, text: "(Something went wrong reaching Synthia. Please try again.)" } : m
        )
      );
      setSending(false);
    }
  }

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header style={{ padding: "0.75rem 1rem", borderBottom: "1px solid #e5e5e5" }}>
          <strong>Synthia</strong>
          <span style={{ color: "#888", marginLeft: "0.5rem", fontSize: "0.85rem" }}>
            your tax return, one conversation at a time
          </span>
        </header>
        <ChatWindow messages={messages} />
        <FieldConfirmationPanel fields={fields} onChanged={refreshFields} />
        <UploadWidget taxReturnId={taxReturnId} onUploaded={refreshFields} />
        <ChatInput disabled={!sessionId || sending} onSend={handleSend} />
      </div>
      <div style={{ width: "280px", borderLeft: "1px solid #e5e5e5", overflowY: "auto" }}>
        <ReturnSummary taxReturnId={taxReturnId} />
        <PriorYearPanel taxReturnId={taxReturnId} />
      </div>
    </div>
  );
}
