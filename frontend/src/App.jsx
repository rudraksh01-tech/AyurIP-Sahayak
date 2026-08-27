import { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const askQuestion = async () => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setAnswer("");
    setSources([]);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      setAnswer(data.answer || "No answer received.");
      setSources(data.sources || []);
    } catch (err) {
      console.error(err);
      setError(
        "Could not connect to AyurIP Sahayak. Make sure the FastAPI backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  };

  const clearChat = () => {
    setQuestion("");
    setAnswer("");
    setSources([]);
    setError("");
  };

  const askExample = (text) => {
    setQuestion(text);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="logo">🌿</div>

          <div>
            <h1>AyurIP Sahayak</h1>
            <p>
              AI-powered Ayurveda & Intellectual Property Research Assistant
            </p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <span className="eyebrow">
            AYURVEDA • TRADITIONAL KNOWLEDGE • IPR
          </span>

          <h2>
            Ask questions.
            <br />
            <span>Discover knowledge.</span>
          </h2>

          <p className="hero-text">
            Search your Ayurveda and Traditional Knowledge documents using
            semantic retrieval and AI-powered answers.
          </p>
        </section>

        <section className="search-card">
          <div className="card-top">
            <div>
              <h3>What would you like to know?</h3>
              <p>
                Ask a question about Ayurveda, TKDL, patents, IPR or
                traditional knowledge.
              </p>
            </div>

            {(answer || error) && (
              <button className="clear-btn" onClick={clearChat}>
                Clear
              </button>
            )}
          </div>

          <div className="input-wrapper">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Example: What is TKDL?"
              rows="4"
              disabled={loading}
            />

            <div className="input-bottom">
              <span>Press Enter to ask • Shift + Enter for a new line</span>

              <button
                className="ask-btn"
                onClick={askQuestion}
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Searching...
                  </>
                ) : (
                  <>
                    Ask Sahayak
                    <span>→</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {!answer && !error && !loading && (
          <section className="examples">
            <p className="examples-title">Try asking</p>

            <div className="example-grid">
              <button
                onClick={() =>
                  askExample(
                    "What is Traditional Knowledge Digital Library (TKDL)?"
                  )
                }
              >
                <span>📚</span>
                <div>
                  <strong>What is TKDL?</strong>
                  <small>Traditional Knowledge Digital Library</small>
                </div>
              </button>

              <button
                onClick={() =>
                  askExample(
                    "What is defensive protection of traditional knowledge?"
                  )
                }
              >
                <span>🛡️</span>
                <div>
                  <strong>What is defensive protection?</strong>
                  <small>Traditional knowledge & IPR</small>
                </div>
              </button>

              <button
                onClick={() =>
                  askExample(
                    "How does traditional knowledge affect patents?"
                  )
                }
              >
                <span>⚖️</span>
                <div>
                  <strong>TK and patents</strong>
                  <small>Prior art & patent protection</small>
                </div>
              </button>
            </div>
          </section>
        )}

        {loading && (
          <section className="answer-card loading-card">
            <div className="answer-header">
              <div className="answer-icon">✦</div>

              <div>
                <span>AYURIP SAHAYAK</span>
                <h3>Researching your question...</h3>
              </div>
            </div>

            <div className="loading-lines">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </section>
        )}

        {error && !loading && (
          <section className="answer-card error-card">
            <div className="answer-header">
              <div className="answer-icon">!</div>

              <div>
                <span>CONNECTION ERROR</span>
                <h3>Unable to get an answer</h3>
              </div>
            </div>

            <p>{error}</p>
          </section>
        )}

        {answer && !loading && (
          <section className="answer-card">
            <div className="answer-header">
              <div className="answer-icon">✦</div>

              <div>
                <span>AYURIP SAHAYAK</span>
                <h3>Research Result</h3>
              </div>
            </div>

            <div className="question-preview">
              <span>You asked</span>
              <p>{question}</p>
            </div>

            <div className="answer-content">
              {answer.split("\n").map((line, index) => (
                <p key={index}>{line || "\u00A0"}</p>
              ))}
            </div>

            {sources.length > 0 && (
              <div className="sources-section">
                <div className="sources-heading">
                  <span className="sources-icon">📚</span>

                  <div>
                    <h3>Sources</h3>
                    <p>
                      Retrieved from your AyurIP Sahayak knowledge base
                    </p>
                  </div>
                </div>

                <div className="sources-list">
                  {sources.map((source, index) => (
                    <div className="source-item" key={`${source.source}-${index}`}>
                      <div className="source-number">{index + 1}</div>

                      <div className="source-info">
                        <strong>{source.source}</strong>

                        <div className="source-meta">
                          <span>Chunk {source.chunk_id}</span>
                          <span>•</span>
                          <span>Relevance {source.score}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <span>AyurIP Sahayak</span>
        <span>•</span>
        <span>RAG-powered research assistant</span>
      </footer>
    </div>
  );
}

export default App;


