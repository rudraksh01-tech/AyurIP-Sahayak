const EXAMPLES = [
  {
    icon: "📚",
    title: "What is TKDL?",
    subtitle: "Traditional Knowledge Digital Library",
    question: "What is the Traditional Knowledge Digital Library (TKDL) and how does it prevent wrongful patents?",
  },
  {
    icon: "⚖️",
    title: "The turmeric patent case",
    subtitle: "A landmark biopiracy dispute",
    question: "What happened in the turmeric patent case?",
  },
  {
    icon: "🛡️",
    title: "Defensive vs positive protection",
    subtitle: "Two ways to protect traditional knowledge",
    question: "What is the difference between defensive and positive protection of traditional knowledge?",
  },
  {
    icon: "अ",
    title: "आयुर्वेद में तीन दोष कौन से हैं?",
    subtitle: "Ask in Hindi or Hinglish too",
    question: "आयुर्वेद में तीन दोष कौन से हैं?",
  },
];

const STEPS = [
  { title: "Understand", text: "Your question is embedded with Gemini, in English or Hindi." },
  { title: "Retrieve", text: "The closest passages are found by semantic search." },
  { title: "Answer", text: "Gemini writes an answer only from those passages." },
  { title: "Verify", text: "Click a citation to see the exact page it came from." },
];

function knowledgeBaseSummary(health) {
  if (health.status !== "online" || !health.documents) {
    return null;
  }

  const pages = health.documents.reduce((total, document) => total + document.pages, 0);

  return `${health.documents.length} documents · ${pages} pages · ${health.chunks} passages`;
}

export default function EmptyState({ health, onAsk }) {
  const summary = knowledgeBaseSummary(health);

  return (
    <section className="empty-state">
      <div className="hero">
        <span className="eyebrow">AI research assistant</span>

        <h1>
          Ask about Ayurveda &amp; IP.
          <br />
          <span>Get answers with sources.</span>
        </h1>

        <p className="hero-text">
          Answers are grounded in a curated knowledge base on Ayurveda,
          Traditional Knowledge, TKDL and Intellectual Property Rights, and
          every claim links back to the page it came from.
        </p>

        {summary && <p className="kb-summary">{summary}</p>}
      </div>

      <div className="example-grid">
        {EXAMPLES.map((example) => (
          <button
            key={example.title}
            className="example-card"
            onClick={() => onAsk(example.question)}
          >
            <span className="example-icon" aria-hidden="true">{example.icon}</span>
            <span>
              <strong>{example.title}</strong>
              <small>{example.subtitle}</small>
            </span>
          </button>
        ))}
      </div>

      <ol className="steps">
        {STEPS.map((step, index) => (
          <li key={step.title}>
            <span className="step-number">{index + 1}</span>
            <span>
              <strong>{step.title}</strong>
              <small>{step.text}</small>
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
