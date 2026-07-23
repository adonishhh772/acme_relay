import { API_URL } from "./config";

export type GroundednessPayload = {
  passed: boolean;
  unsupported_claims: string[];
  evidence_ids_used: string[];
  explanation: string;
};

export type ChatResponse = {
  answer: string;
  session_id: string;
  request_id: string;
  tools_used: string[];
  pending_approvals: Array<Record<string, unknown>>;
  prompt_name: string;
  prompt_version: number;
  latency_ms: number;
  grounded?: boolean | null;
  groundedness?: GroundednessPayload | null;
};

export type RunProgressEvent = {
  type: string;
  at?: string;
  request_id?: string;
  tool?: string;
  source?: string;
  label?: string;
  plan?: string[];
  agent?: string;
  latency_ms?: number;
  status?: string;
};

export type ChatStreamHandlers = {
  onStarted?: (requestId: string) => void;
  onProgress?: (event: RunProgressEvent) => void;
};

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block.split("\n");
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }
  if (dataLines.length === 0) {
    return null;
  }
  return { event, data: dataLines.join("\n") };
}

export async function streamChat(
  query: string,
  token: string,
  sessionId: string | null,
  handlers: ChatStreamHandlers = {},
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ query, session_id: sessionId }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Chat stream failed (${response.status})`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming body unavailable");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let finalResponse: ChatResponse | null = null;

  function processBlock(block: string) {
    const parsed = parseSseBlock(block);
    if (!parsed) {
      return;
    }
    if (parsed.event === "started") {
      const payload = JSON.parse(parsed.data) as { request_id?: string };
      if (payload.request_id) {
        handlers.onStarted?.(payload.request_id);
      }
      return;
    }
    if (parsed.event === "progress") {
      handlers.onProgress?.(JSON.parse(parsed.data) as RunProgressEvent);
      return;
    }
    if (parsed.event === "done") {
      finalResponse = JSON.parse(parsed.data) as ChatResponse;
      return;
    }
    if (parsed.event === "error") {
      const payload = JSON.parse(parsed.data) as { message?: string };
      throw new Error(payload.message || "Chat stream error");
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      if (part.trim()) {
        processBlock(part);
      }
    }
  }
  if (buffer.trim()) {
    processBlock(buffer);
  }

  if (!finalResponse) {
    throw new Error("Stream ended without a done event");
  }
  return finalResponse;
}
