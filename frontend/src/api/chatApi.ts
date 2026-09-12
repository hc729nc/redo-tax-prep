import { apiClient } from "./client";

const BASE_URL = "http://localhost:8000";

export interface ChatSession {
  id: string;
  tax_return_id: string;
}

export const chatApi = {
  createSession: (taxReturnId: string) =>
    apiClient.request<ChatSession>("/api/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ tax_return_id: taxReturnId }),
    }),

  streamMessage: async (
    sessionId: string,
    text: string,
    onToken: (token: string) => void,
    onDone: () => void
  ): Promise<void> => {
    const res = await fetch(`${BASE_URL}/api/chat/sessions/${sessionId}/messages/stream`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok || !res.body) {
      throw new Error(`Chat stream failed: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const line = event.trim();
        if (!line.startsWith("data:")) continue;
        const payload = JSON.parse(line.slice(5).trim());
        if (payload.type === "token") {
          onToken(payload.text);
        } else if (payload.type === "done") {
          onDone();
        }
      }
    }
  },
};
