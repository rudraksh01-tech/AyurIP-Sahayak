import { useState } from "react";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      setAnswer(data.answer);
    } catch (error) {
      setAnswer("❌ Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "900px", margin: "50px auto", padding: "20px" }}>
      <h1>🌿 AyurIP-Sahayak</h1>

      <p>
        🤖 AI Assistant for Ayurveda, Traditional Knowledge & IPR
      </p>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask your question..."
        rows="5"
        style={{
          width: "100%",
          padding: "15px",
          fontSize: "16px",
          boxSizing: "border-box",
        }}
      />

      <button
        onClick={askQuestion}
        disabled={loading}
        style={{
          marginTop: "15px",
          padding: "12px 25px",
          fontSize: "16px",
          cursor: "pointer",
        }}
      >
        {loading ? "🔎 Searching..." : "Ask AyurIP-Sahayak"}
      </button>

      {answer && (
        <div
          style={{
            marginTop: "30px",
            padding: "20px",
            border: "1px solid #ddd",
            borderRadius: "10px",
            whiteSpace: "pre-wrap",
          }}
        >
          <h2>💬 Answer</h2>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}

export default App;