import { useState } from "react";

import { ChevronIcon } from "./Icons.jsx";

function SourceCard({ id, source, cited, active }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li
      id={id}
      className={`source-card${cited ? " is-cited" : ""}${active ? " is-active" : ""}`}
    >
      <div className="source-top">
        <span className="source-number">{source.number}</span>

        <div className="source-meta">
          <strong>{source.title}</strong>
          <span>
            Page {source.page}
            {source.section && ` · ${source.section}`}
          </span>
        </div>

        {cited && <span className="badge">Cited</span>}
      </div>

      <p className={`source-text${expanded ? " is-expanded" : ""}`}>{source.text}</p>

      <div className="source-footer">
        <button className="link-button" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less" : "Show full passage"}
        </button>

        {source.similarity != null && (
          <span className="source-score">Similarity {source.similarity.toFixed(2)}</span>
        )}
      </div>
    </li>
  );
}

export default function SourceList({ messageId, sources, cited, open, activeSource, onToggle }) {
  return (
    <div className="sources">
      <button className="sources-toggle" onClick={onToggle} aria-expanded={open}>
        <span>
          {sources.length} sources
          {cited.length > 0 && ` · ${cited.length} cited`}
        </span>
        <ChevronIcon size={16} className={open ? "is-open" : undefined} />
      </button>

      {open && (
        <ol className="source-list">
          {sources.map((source) => (
            <SourceCard
              key={source.chunk_id}
              id={`${messageId}-source-${source.number}`}
              source={source}
              cited={cited.includes(source.number)}
              active={activeSource === source.number}
            />
          ))}
        </ol>
      )}
    </div>
  );
}
