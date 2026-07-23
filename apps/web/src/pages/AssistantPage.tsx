import {
  ArrowUp,
  CheckCircle2,
  Loader2,
  MessageSquare,
  Radio,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { useState, type ChangeEvent, type KeyboardEvent } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import {
  streamChat,
  type ChatResponse,
  type GroundednessPayload,
  type RunProgressEvent,
} from "../lib/chatStream";
import { useAuth } from "../providers/AuthProvider";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  tools?: string[];
  groundedness?: GroundednessPayload | null;
  latencyMs?: number;
};

const SUGGESTIONS = [
  "Show open cases for VaultLedger Payments and suggest the next action.",
  "Who is the account owner for VaultLedger Payments and when is renewal?",
  "What is the SLA risk on OPS-3101?",
  "Summarise Nexus Freight open issues.",
];

function progressLabel(event: RunProgressEvent): string {
  if (event.type === "tool_start" && event.tool) {
    return `Calling ${event.tool}`;
  }
  if (event.type === "tool_done" && event.tool) {
    return `Finished ${event.tool}${event.latency_ms != null ? ` (${event.latency_ms}ms)` : ""}`;
  }
  if (event.type === "plan" && event.plan?.length) {
    return `Plan: ${event.plan.join(" → ")}`;
  }
  if (event.label) {
    return event.label;
  }
  if (event.agent) {
    return `Agent: ${event.agent}`;
  }
  return event.type;
}

export function AssistantPage() {
  const { token } = useAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progressSteps, setProgressSteps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function sendQuery(query: string) {
    if (!token || !query.trim() || isLoading) {
      return;
    }
    const trimmed = query.trim();
    setInput("");
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setIsLoading(true);
    setError(null);
    setProgressSteps([]);
    try {
      const response: ChatResponse = await streamChat(trimmed, token, sessionId, {
        onProgress(event) {
          setProgressSteps((current) => {
            const next = progressLabel(event);
            if (current[current.length - 1] === next) {
              return current;
            }
            return [...current.slice(-8), next];
          });
        },
      });
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          tools: response.tools_used,
          groundedness: response.groundedness,
          latencyMs: response.latency_ms,
        },
      ]);
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
      setProgressSteps([]);
    }
  }

  function handleSend() {
    void sendQuery(input);
  }

  function handleInputChange(event: ChangeEvent<HTMLTextAreaElement>) {
    setInput(event.target.value);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  return (
    <div
      className="flex h-full min-h-[calc(100vh-3.5rem)] flex-col lg:min-h-screen"
      data-testid="assistant-page"
    >
      <div className="border-b border-surface-border bg-white px-6 py-5 lg:px-8">
        <PageHeader
          icon={MessageSquare}
          title="Assistant"
          description="Streams tool activity, then verifies claims against tool evidence."
          className="mb-0"
        />
      </div>

      <div className="flex-1 overflow-y-auto bg-relay-mesh px-4 py-6 lg:px-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-4" data-testid="chat-log">
          {messages.length === 0 && !isLoading ? (
            <div className="card mx-auto max-w-xl p-8 text-center">
              <Radio className="mx-auto h-7 w-7 text-relay-cyan" />
              <h2 className="mt-4 font-display text-xl font-semibold">Ask the desk</h2>
              <p className="mt-2 text-sm text-ink-secondary">
                VaultLedger, Nexus Freight, or Aurora Bank — Relay will show tool steps while it works.
              </p>
              <div className="mt-6 grid gap-2 text-left">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    className="chip"
                    onClick={() => void sendQuery(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {messages.map((message, index) =>
            message.role === "user" ? (
              <div
                key={`user-${index}`}
                className="ml-auto max-w-[85%] rounded-2xl bg-relay-slate px-4 py-3 text-sm text-white"
              >
                {message.content}
              </div>
            ) : (
              <article key={`assistant-${index}`} className="card max-w-[94%] overflow-hidden">
                <div className="border-b border-surface-border bg-surface-muted/50 px-4 py-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    {message.groundedness?.passed ? (
                      <span
                        className="inline-flex items-center gap-1.5 rounded-full bg-teal-500/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-teal-700"
                        data-testid="groundedness-pass"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Groundedness verified
                      </span>
                    ) : (
                      <span
                        className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-amber-700"
                        data-testid="groundedness-review"
                      >
                        <ShieldAlert className="h-3.5 w-3.5" />
                        Needs review
                      </span>
                    )}
                    {message.latencyMs != null ? (
                      <span className="text-xs text-ink-muted">{message.latencyMs} ms</span>
                    ) : null}
                  </div>
                  {message.groundedness?.explanation ? (
                    <p className="mt-2 text-xs leading-relaxed text-ink-secondary">
                      {message.groundedness.explanation}
                    </p>
                  ) : null}
                  {message.groundedness?.unsupported_claims?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-amber-800">
                      {message.groundedness.unsupported_claims.map((claim) => (
                        <li key={claim}>{claim}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
                <div className="whitespace-pre-wrap px-4 py-4 text-sm leading-relaxed text-ink-primary">
                  {message.content}
                </div>
                {message.tools?.length ? (
                  <div className="flex flex-wrap gap-2 border-t border-surface-border px-4 py-3">
                    {message.tools.map((toolName) => (
                      <span
                        key={toolName}
                        className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[11px] text-slate-700"
                      >
                        <Wrench className="h-3 w-3" />
                        {toolName}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ),
          )}

          {isLoading ? (
            <div className="card max-w-[94%] p-4" data-testid="agent-activity">
              <div className="flex items-center gap-2 text-sm font-medium text-ink-primary">
                <Loader2 className="h-4 w-4 animate-spin text-relay-cyan" />
                Working…
              </div>
              <ol className="mt-3 space-y-1.5">
                {progressSteps.length === 0 ? (
                  <li className="text-xs text-ink-muted">Starting agent run…</li>
                ) : (
                  progressSteps.map((step, index) => (
                    <li key={`${step}-${index}`} className="font-mono text-xs text-ink-secondary">
                      {step}
                    </li>
                  ))
                )}
              </ol>
            </div>
          ) : null}
        </div>
      </div>

      <div className="border-t border-surface-border bg-white p-4">
        <div className="mx-auto flex max-w-3xl items-end gap-3 rounded-2xl border border-surface-border bg-surface-muted/40 p-3">
          <textarea
            data-testid="chat-input"
            className="form-input min-h-[56px] flex-1 resize-none border-0 bg-transparent shadow-none focus:ring-0"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleComposerKeyDown}
            placeholder="Ask about a customer or case…"
          />
          <button
            type="button"
            className="btn-primary h-11 w-11 shrink-0 !px-0"
            data-testid="chat-send"
            disabled={isLoading || !input.trim()}
            onClick={handleSend}
            aria-label="Send"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
        {error ? <p className="error-text mx-auto mt-3 max-w-3xl">{error}</p> : null}
      </div>
    </div>
  );
}
