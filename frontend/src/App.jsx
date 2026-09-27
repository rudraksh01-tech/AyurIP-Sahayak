import { useEffect, useRef, useState } from "react";

import "./App.css";
import { fetchHealth, streamAnswer } from "./api.js";
import ChatMessage from "./components/ChatMessage.jsx";
import Composer from "./components/Composer.jsx";
import EmptyState from "./components/EmptyState.jsx";
import Header from "./components/Header.jsx";

// Earlier turns sent along so follow-up questions ("and neem?") make sense
const HISTORY_TURNS = 6;

let nextId = 0;
const newId = () => `m${++nextId}`;

function isNearBottom() {
  return window.innerHeight + window.scrollY >= document.body.scrollHeight - 160;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [health, setHealth] = useState({ status: "checking" });
  const controllerRef = useRef(null);
  const endRef = useRef(null);
  const followRef = useRef(true);

  const busy = messages.some(
    (message) => message.status === "searching" || message.status === "streaming"
  );

  useEffect(() => {
    fetchHealth()
      // The API's own "status": "healthy" must not replace ours
      .then((data) => setHealth({ ...data, status: "online" }))
      .catch(() => setHealth({ status: "offline" }));
  }, []);

  // Keep the newest text in view while streaming, unless the user scrolled up
  useEffect(() => {
    if (followRef.current) {
      endRef.current?.scrollIntoView({ block: "end" });
    }
  }, [messages]);

  useEffect(() => {
    const onScroll = () => {
      followRef.current = isNearBottom();
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const updateMessage = (id, update) => {
    setMessages((previous) =>
      previous.map((message) =>
        message.id === id
          ? { ...message, ...(typeof update === "function" ? update(message) : update) }
          : message
      )
    );
  };

  const ask = async (text, earlierMessages = messages) => {
    const question = text.trim();

    if (!question || busy) {
      return;
    }

    const history = earlierMessages
      .filter((message) => message.role === "user" || message.status === "done")
      .slice(-HISTORY_TURNS)
      .map(({ role, content }) => ({ role, content }));

    const assistantId = newId();

    setMessages([
      ...earlierMessages,
      { id: newId(), role: "user", content: question },
      { id: assistantId, role: "assistant", content: "", sources: [], cited: [], status: "searching" },
    ]);
    setInput("");
    followRef.current = true;

    const controller = new AbortController();
    controllerRef.current = controller;

    const handleEvent = (event) => {
      if (event.type === "sources") {
        updateMessage(assistantId, {
          sources: event.sources,
          retrievalMs: event.retrieval_ms,
          status: "streaming",
        });
      } else if (event.type === "delta") {
        updateMessage(assistantId, (message) => ({ content: message.content + event.text }));
      } else if (event.type === "done") {
        updateMessage(assistantId, {
          cited: event.cited,
          generationMs: event.generation_ms,
          status: "done",
        });
      } else if (event.type === "error") {
        updateMessage(assistantId, { status: "error", error: event.message });
      }
    };

    try {
      await streamAnswer({ question, history, signal: controller.signal, onEvent: handleEvent });
      setHealth((current) => (current.status === "offline" ? { ...current, status: "online" } : current));
    } catch (error) {
      if (error.name === "AbortError") {
        updateMessage(assistantId, (message) => ({ status: message.content ? "done" : "stopped" }));
      } else {
        updateMessage(assistantId, { status: "error", error: error.message });
      }
    } finally {
      // A dropped connection can end the stream without a "done" event
      updateMessage(assistantId, (message) =>
        message.status === "searching" || message.status === "streaming" ? { status: "done" } : {}
      );
      controllerRef.current = null;
    }
  };

  const stop = () => controllerRef.current?.abort();

  const newChat = () => {
    stop();
    setMessages([]);
    setInput("");
  };

  const retry = (assistantId) => {
    const index = messages.findIndex((message) => message.id === assistantId);
    const question = messages[index - 1];

    ask(question.content, messages.slice(0, index - 1));
  };

  return (
    <div className="app">
      <Header health={health} hasMessages={messages.length > 0} onNewChat={newChat} />

      <main className="main">
        {messages.length === 0 ? (
          <EmptyState health={health} onAsk={(question) => ask(question)} />
        ) : (
          <div className="conversation">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onRetry={() => retry(message.id)}
              />
            ))}
            <div ref={endRef} />
          </div>
        )}
      </main>

      <Composer
        value={input}
        onChange={setInput}
        onSubmit={() => ask(input)}
        onStop={stop}
        busy={busy}
      />
    </div>
  );
}

export default App;
