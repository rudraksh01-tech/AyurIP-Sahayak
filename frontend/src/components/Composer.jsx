import { useEffect, useRef } from "react";

import { SearchIcon, SendIcon, StopIcon } from "./Icons.jsx";

const MAX_LENGTH = 500;

/**
 * variant "hero": large search box on the home page.
 * variant "dock": sticky input at the bottom of a conversation.
 */
export default function Composer({ value, onChange, onSubmit, onStop, busy, variant = "dock" }) {
  const textareaRef = useRef(null);

  // Grow with the text, up to the max-height set in CSS
  useEffect(() => {
    const textarea = textareaRef.current;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }, [value]);

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit();
  };

  const form = (
    <form className={`composer composer-${variant}`} onSubmit={handleSubmit}>
      {variant === "hero" && <SearchIcon size={20} className="composer-icon" />}

      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          variant === "hero"
            ? "Ask about Ayurveda, TKDL, patents or traditional knowledge…"
            : "Ask a follow-up question…"
        }
        rows={1}
        maxLength={MAX_LENGTH}
        aria-label="Your question"
        autoFocus
      />

      {busy ? (
        <button type="button" className="send-button" onClick={onStop} aria-label="Stop answering">
          <StopIcon size={16} />
        </button>
      ) : (
        <button type="submit" className="send-button" disabled={!value.trim()} aria-label="Ask">
          <SendIcon size={18} />
        </button>
      )}
    </form>
  );

  if (variant === "hero") {
    return form;
  }

  return (
    <div className="composer-dock">
      {form}
      <p className="composer-note">
        Answers come only from the knowledge base and may be incomplete. Not legal or medical advice.
      </p>
    </div>
  );
}
