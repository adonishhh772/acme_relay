import { useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type ChatMessage = { role: "user" | "assistant"; content: string };

type ChatResponse = {
  answer: string;
  tools_used: string[];
  pending_approvals: Array<Record<string, unknown>>;
  latency_ms: number;
  session_id: string;
};

export function AssistantPage() {
  const { token } = useAuth();
  const [input, setInput] = useState(
    "Show open cases for Meridian Pay, summarise latest status, and suggest the next action.",
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [tools, setTools] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!token || !input.trim() || isLoading) return;
    const query = input.trim();
    setInput("");
    setMessages((current) => [...current, { role: "user", content: query }]);
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiFetch<ChatResponse>("/api/chat", token, {
        method: "POST",
        body: JSON.stringify({ query, session_id: sessionId }),
      });
      setSessionId(response.session_id);
      setTools(response.tools_used);
      setMessages((current) => [...current, { role: "assistant", content: response.answer }]);
      if (response.pending_approvals?.length) {
        for (const approval of response.pending_approvals) {
          await apiFetch("/api/approvals/stage", token, {
            method: "POST",
            body: JSON.stringify({ approval }),
          });
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div data-testid="assistant-page">
      <h1>Assistant</h1>
      <p style={{ color: "var(--ink-muted)" }}>
        Relay reasons with tools against Postgres, Redis session memory, and RBAC-aware RAG.
      </p>
      <div className="panel">
        <div className="chat-log" data-testid="chat-log">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
              {message.content}
            </div>
          ))}
        </div>
        <div className="composer">
          <textarea
            data-testid="chat-input"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about Meridian Pay, Cascade Retail, or Northline Logistics…"
          />
          <button
            type="button"
            className="btn"
            data-testid="chat-send"
            disabled={isLoading}
            onClick={() => {
              void handleSend();
            }}
          >
            {isLoading ? "Working…" : "Send"}
          </button>
        </div>
        {tools.length ? (
          <p className="mono" style={{ marginTop: "1rem", fontSize: "0.8rem" }}>
            Tools: {tools.join(", ")}
          </p>
        ) : null}
        {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      </div>
    </div>
  );
}
