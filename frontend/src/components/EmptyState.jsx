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
  SparkleIcon,
} from "./Icons.jsx";

const TOPIC_ICONS = {
  leaf: LeafIcon,
  book: BookIcon,
  scale: ScaleIcon,
  landmark: LandmarkIcon,
  globe: GlobeIcon,
  search: SearchIcon,
};

const PROMISES = [
  {
    icon: QuoteIcon,
    title: "Page-level citations",
    text: "Every claim links to the document, page and section it came from.",
  },
  {
    icon: ShieldIcon,
    title: "No guessing",
    text: "If the sources don't cover a question, Sahayak says so instead of inventing an answer.",
  },
  {
    icon: LanguagesIcon,
    title: "English, हिन्दी, Hinglish",
    text: "Ask in the language you think in; the answer comes back in the same one.",
  },
];

function Stats({ health }) {
  if (health.status !== "online" || !health.documents) {
    return null;
  }

  const pages = health.documents.reduce((total, document) => total + document.pages, 0);

  const stats = [
    [health.documents.length, "curated sources"],
    [pages, "pages indexed"],
    [health.chunks, "searchable passages"],
  ];

  return (
    <dl className="stats">
      {stats.map(([value, label]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function TopicCard({ topic, onAsk }) {
  const Icon = TOPIC_ICONS[topic.icon];

  return (
    <article className="topic-card glass">
      <div className="topic-head">
        <span className={`topic-icon topic-icon-${topic.id}`}>
          <Icon size={20} />
        </span>
        <div>
          <h3>{topic.title}</h3>
          <p>{topic.description}</p>
        </div>
      </div>

      <ul className="topic-questions">
        {topic.questions.map((question) => (
          <li key={question}>
            <button onClick={() => onAsk(question)}>
              <span>{question}</span>
              <ArrowRightIcon size={15} />
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
        <article key={document.title} className="doc-card glass">
          <span className="doc-icon">
            <FileIcon size={20} />
          </span>
          <div>
            <h3>{document.full_title || document.title}</h3>
            {document.author && <p className="doc-author">{document.author}</p>}
            <p className="doc-meta">
              {document.pages} pages · {document.chunks} passages
            </p>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function EmptyState({ health, onAsk, composer }) {
  return (
    <div className="home">
      <section className="hero">
        <span className="eyebrow glass">
          <SparkleIcon size={14} />
          AI research assistant for Indian knowledge &amp; IP
        </span>

        <h1>
          Research Ayurveda &amp; IP law
          <span className="gradient-text"> with answers you can verify.</span>
        </h1>

        <p className="hero-text">
          Ask in English, हिन्दी or Hinglish. Sahayak searches a curated knowledge
          base and cites the exact page behind every claim.
        </p>

        <div className="hero-composer">{composer}</div>

        <div className="suggestions" aria-label="Suggested questions">
          {SUGGESTIONS.map((question) => (
            <button key={question} className="chip glass" onClick={() => onAsk(question)}>
              {question}
            </button>
          ))}
        </div>

        <Stats health={health} />
      </section>

      <section className="section" aria-labelledby="topics-heading">
        <div className="section-head">
          <span className="kicker">Explore</span>
          <h2 id="topics-heading">Start from a topic</h2>
          <p>Pick a question to see how Sahayak answers. Every topic is covered by the sources.</p>
        </div>

        <div className="topic-grid">
          {TOPICS.map((topic) => (
            <TopicCard key={topic.id} topic={topic} onAsk={onAsk} />
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="sources-heading">
        <div className="section-head">
          <span className="kicker">Trust</span>
          <h2 id="sources-heading">Grounded in real sources</h2>
          <p>Answers are written only from these documents, never from the model's memory.</p>
        </div>

        <SourceDocuments health={health} />

        <div className="promise-grid">
          {PROMISES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="promise glass">
              <span className="promise-icon">
                <Icon size={18} />
              </span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
