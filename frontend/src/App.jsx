import { useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  const checkBackend = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/");
      const data = await response.json();

      setMessage(data.message);
    } catch (error) {
      setMessage("Backend se connection nahi ho paaya.");
      console.error(error);
    }
  };

  return (
    <div>
      <h1>AyurIP Sahayak</h1>

      <p>AI-powered Ayurveda IP Research Assistant</p>

      <button onClick={checkBackend}>
        Check Backend
      </button>

      {message && <p>{message}</p>}
    </div>
  );
}

export default App;