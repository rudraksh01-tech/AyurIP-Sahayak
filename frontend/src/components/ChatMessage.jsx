import { useEffect, useState } from "react";

import AnswerMarkdown from "./AnswerMarkdown.jsx";
import { CheckIcon, CopyIcon, LeafIcon, RetryIcon } from "./Icons.jsx";
import SourceList from "./SourceList.jsx";

function formatSeconds(ms) {
  return `${(ms / 1000).toFixed(1)}s`;
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard can be blocked (e.g. insecure context); nothing to do
    }
  };

  return (
    <button className="icon-button" onClick={copy} aria-label="Copy answer" title="Copy answer">
      {copied ? <CheckIcon size={15} /> : <CopyIcon size={15} />}
    </button>
  );
}

function AssistantMessage({ message, onRetry }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [activeSource, setActiveSource] = useState(null);

  const showCitation = (number) => {
    setSourcesOpen(true);
    setActiveSource(number);
  };

  // Bring the clicked source into view once the list has rendered
  useEffect(() => {
    if (activeSource == null) {
      return;
    }

    document
      .getElementById(`${message.id}-source-${activeSource}`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeSource, message.id]);

  const { status, content, sources } = message;
  const isWorking = status === "searching" || status === "streaming";

  return (
    <article className="message message-assistant">
      <div className="avatar" aria-hidden="true">
        <LeafIcon size={16} />
      </div>

      <div className="message-body">
        {status === "searching" && (
          <p className="thinking">
            <span className="dots" aria-hidden="true"><span /><span /><span /></span>
            Searching the knowledge base…
          </p>
        )}

        {status === "streaming" && !content && (
          <p className="thinking">
            <span className="dots" aria-hidden="true"><span /><span /><span /></span>
            Reading {sources.length} passages…
          </p>
        )}

        {content && (
          <AnswerMarkdown text={content} sourceCount={sources.length} onCite={showCitation} />
        )}

        {status === "streaming" && content && <span className="caret" aria-hidden="true" />}

        {status === "stopped" && <p className="message-note">Stopped.</p>}

        {status === "error" && (
          <div className="error-box" role="alert">
            <p>{message.error}</p>
            <button className="button button-ghost" onClick={onRetry}>
              <RetryIcon size={15} />
              Try again
            </button>
          </div>
        )}

        {!isWorking && content && (
          <div className="message-actions">
            <CopyButton text={content} />

            {message.generationMs != null && (
              <span className="message-meta">
                Answered in {formatSeconds(message.retrievalMs + message.generationMs)}
              </span>
            )}
          </div>
        )}

        {/* Sources arrive before the answer, so citations are clickable while it streams */}
        {sources.length > 0 && status !== "searching" && (
          <SourceList
            messageId={message.id}
            sources={sources}
            cited={message.cited}
            open={sourcesOpen}
            activeSource={activeSource}
            onToggle={() => setSourcesOpen(!sourcesOpen)}
          />
        )}
      </div>
    </article>
  );
}

export default function ChatMessage({ message, onRetry }) {
  if (message.role === "user") {
    return (
      <article className="message message-user">
        <p>{message.content}</p>
      </article>
    );
  }

  return <AssistantMessage message={message} onRetry={onRetry} />;
}
