// Same origin by default (Vite proxies /api in development). Set
// VITE_API_URL in frontend/.env to call a backend hosted elsewhere.
const API_URL = import.meta.env.VITE_API_URL || "";

const CONNECTION_ERROR =
  "Could not connect to AyurIP Sahayak. Please check your connection and try again.";

function errorMessage(detail, status) {
  // FastAPI validation errors arrive as a list of {msg, loc, ...}
  if (Array.isArray(detail)) {
    return detail[0]?.msg?.replace(/^Value error, /, "") || "Invalid question.";
  }

  return detail || `Server error (${status}). Please try again.`;
}

export async function fetchHealth() {
  const response = await fetch(`${API_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }

  return response.json();
}

/**
 * Ask a question and receive the answer as a stream of events:
 *   {type: "sources", sources, retrieval_ms}
 *   {type: "delta", text}          (many)
 *   {type: "done", cited, generation_ms}
 *   {type: "error", message}
 */
export async function streamAnswer({ question, history, signal, onEvent }) {
  let response;

  try {
    response = await fetch(`${API_URL}/api/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history }),
      signal,
    });
  } catch (error) {
    // fetch() only throws a TypeError when the server can't be reached
    throw error instanceof TypeError ? new Error(CONNECTION_ERROR) : error;
  }

  if (!response.ok) {
    // Error responses are not always JSON (e.g. a proxy's HTML error page)
    const data = await response.json().catch(() => ({}));
    throw new Error(errorMessage(data.detail, response.status));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop();

    for (const line of lines) {
      if (line.trim()) {
        onEvent(JSON.parse(line));
      }
    }
  }

  if (buffer.trim()) {
    onEvent(JSON.parse(buffer));
  }
}
