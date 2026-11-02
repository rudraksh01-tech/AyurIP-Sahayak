import { useEffect, useRef } from "react";

import { GITHUB_URL } from "../links.js";
import { SUGGESTIONS, TOPICS } from "../topics.js";
import {
  ArrowRightIcon,
  BookIcon,
  FileIcon,
  GlobeIcon,
  LandmarkIcon,
  LanguagesIcon,
  LeafIcon,
  QuoteIcon,
  ScaleIcon,
  SearchIcon,
  ShieldIcon,
} from "./Icons.jsx";

const TOPIC_ICONS = {
  leaf: LeafIcon,
  book: BookIcon,
  scale: ScaleIcon,
  landmark: LandmarkIcon,
  globe: GlobeIcon,
  search: SearchIcon,
};

// From backend/eval (README "Results at a glance"); update after re-running the evals
const METRICS = [
  { value: "0.99", label: "Faithfulness", detail: "166 of 167 answer claims backed by the cited passage" },
  { value: "95%", label: "Right passage first", detail: "Hit@1 on 38 questions in English, Hindi and Kannada" },
  { value: "5/5", label: "Off-topic refused", detail: "Says “not covered” instead of guessing" },
  { value: "<2s", label: "To first words", detail: "Streaming on the live demo, sources first" },
];

const STEPS = [
  {
    icon: SearchIcon,
    title: "Retrieve",
    text: "Your question is embedded and matched against every passage in the knowledge base, in English, Hindi, Kannada or Hinglish.",
  },
  {
    icon: QuoteIcon,
    title: "Cite",
    text: "The answer is written only from the top passages, and every claim links to its document, page and section.",
  },
  {
    icon: ShieldIcon,
    title: "Refuse",
    text: "If the passages don't cover the question, Sahayak says so instead of filling the gap from memory.",
  },
];

// Fade sections in as they scroll into view
function useReveal() {
  const ref = useRef(null);

  useEffect(() => {
    const items = ref.current.querySelectorAll(".reveal");

    if (!("IntersectionObserver" in window)) {
      items.forEach((item) => item.classList.add("is-visible"));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px" }
    );

    items.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return ref;
}

function LiveIndex({ health }) {
  if (health.status !== "online" || !health.documents) {
    return null;
  }

  const pages = health.documents.reduce((total, document) => total + document.pages, 0);

  return (
    <p className="live-index">
      <span className="live-dot" aria-hidden="true" />
      Live index · {health.documents.length} sources · {pages} pages · {health.chunks} passages
    </p>
  );
}

function TopicCard({ topic, index, onAsk }) {
  const Icon = TOPIC_ICONS[topic.icon];

  return (
    <article className="topic-card">
      <div className="topic-head">
        <span className="topic-icon">
          <Icon size={18} />
        </span>
        <span className="topic-index">{String(index + 1).padStart(2, "0")}</span>
      </div>

      <h3>{topic.title}</h3>
      <p>{topic.description}</p>

      <ul className="topic-questions">
        {topic.questions.map((question) => (
          <li key={question}>
            <button onClick={() => onAsk(question)}>
              <span>{question}</span>
              <ArrowRightIcon size={14} />
            </button>
          </li>
        ))}
      </ul>
    </article>
  );
}

function SourceDocuments({ health }) {
  if (health.status !== "online" || !health.documents) {
    return null;
  }

  return (
    <div className="doc-list">
      {health.documents.map((document) => (
        <article key={document.title} className="doc-card">
          <span className="doc-icon">
            <FileIcon size={18} />
          </span>
          <div>
            <h3>{document.full_title || document.title}</h3>
            {document.author && <p className="doc-author">{document.author}</p>}
          </div>
          <p className="doc-meta">
            {document.pages} pp · {document.chunks} passages
          </p>
        </article>
      ))}
    </div>
  );
}

export default function EmptyState({ health, onAsk, composer }) {
  const homeRef = useReveal();

  return (
    <div className="home" ref={homeRef}>
      <section className="hero">
        <span className="eyebrow">
          <span className="eyebrow-tag">RAG</span>
          Grounded answers on Ayurveda &amp; IP law
        </span>

        <h1>
          Research traditional knowledge,
          <em> with answers you can verify.</em>
        </h1>

        <p className="hero-text">
          Ask in English, हिन्दी, ಕನ್ನಡ or Hinglish. Sahayak searches a curated knowledge
          base and cites the exact page behind every claim.
        </p>

        <div className="hero-composer">{composer}</div>

        <div className="suggestions" aria-label="Suggested questions">
          <span className="suggestions-label">Try</span>
          {SUGGESTIONS.map(({ text, lang }) => (
            <button key={text} className="chip" onClick={() => onAsk(text)}>
              <span className="chip-lang">{lang}</span>
              {text}
            </button>
          ))}
        </div>

        <LiveIndex health={health} />
      </section>

      <section className="metrics reveal" aria-labelledby="metrics-heading">
        <div className="metrics-head">
          <div>
            <span className="kicker" id="metrics-heading">Measured, not claimed</span>
            <p>38 labelled questions in four languages · answers checked by a judge model from another family</p>
          </div>
          <a
            className="metrics-link"
            href={`${GITHUB_URL}#answer-quality-evaluation`}
            target="_blank"
            rel="noreferrer"
          >
            Methodology
            <ArrowRightIcon size={13} />
          </a>
        </div>

        <dl className="metric-grid">
          {METRICS.map((metric) => (
            <div key={metric.label} className="metric">
              <dt>{metric.label}</dt>
              <dd>{metric.value}</dd>
              <p>{metric.detail}</p>
            </div>
          ))}
        </dl>
      </section>

      <section className="section" aria-labelledby="topics-heading">
        <div className="section-head reveal">
          <span className="kicker">Explore</span>
          <h2 id="topics-heading">Start from a topic</h2>
          <p>Every question below is covered by the sources, so each one has a cited answer.</p>
        </div>

        <div className="topic-grid reveal">
          {TOPICS.map((topic, index) => (
            <TopicCard key={topic.id} topic={topic} index={index} onAsk={onAsk} />
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="how-heading">
        <div className="section-head reveal">
          <span className="kicker">How it works</span>
          <h2 id="how-heading">Grounded in real sources</h2>
          <p>Answers come only from these documents, never from the model's memory.</p>
        </div>

        <ol className="steps reveal">
          {STEPS.map(({ icon: Icon, title, text }, index) => (
            <li key={title} className="step">
              <div className="step-head">
                <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
                <Icon size={16} />
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>

        <div className="reveal">
          <SourceDocuments health={health} />
        </div>

        <p className="languages-note">
          <LanguagesIcon size={15} />
          Ask in the language you think in; the answer comes back in the same one.
        </p>
      </section>
    </div>
  );
}
