import { useState } from "react";
import FileUpload from "./components/FileUpload";
import QueryInput from "./components/QueryInput";
import QuizView from "./components/QuizView";
import FlashcardView from "./components/FlashcardView";
import ReviewView from "./components/ReviewView";
import { resetSession } from "./api";
import "./App.css";

function ResultView({ result }) {
  if (!result) return null;

  const type = result.type || result.data?.type || "review";

  switch (type) {
    case "quiz":
      return <QuizView data={result.data || result} />;
    case "flashcard":
      return <FlashcardView data={result.data || result} />;
    case "review":
      return <ReviewView data={result} />;
    default:
      return (
        <div className="review-section">
          <h4>Response</h4>
          <pre>{JSON.stringify(result.data || result, null, 2)}</pre>
        </div>
      );
  }
}

export default function App() {
  const [sessionId, setSessionId] = useState(
    () => localStorage.getItem("session_id") || ""
  );
  const [latestResult, setLatestResult] = useState(null);
  const [uploadCount, setUploadCount] = useState(0);

  const handleUploadSuccess = (result) => {
    const sid = result.session_id;
    setSessionId(sid);
    localStorage.setItem("session_id", sid);
    setUploadCount((c) => c + 1);
  };

  const handleResult = (result) => {
    setLatestResult(result);
  };

  const handleReset = async () => {
    if (!sessionId) return;
    try {
      await resetSession(sessionId);
      setSessionId("");
      setLatestResult(null);
      setUploadCount(0);
      localStorage.removeItem("session_id");
    } catch (e) {
      alert("Reset failed: " + e.message);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>📚 Study Assistant</h1>
          <span className="subtitle">Upload docs → Get quizzes, flashcards & reviews</span>
        </div>
        <div className="header-right">
          {sessionId && (
            <>
              <span className="session-badge">
                {uploadCount} doc{uploadCount !== 1 ? "s" : ""} loaded
              </span>
              <button className="btn danger" onClick={handleReset}>
                Reset Session
              </button>
            </>
          )}
        </div>
      </header>

      <main className="app-main">
        <FileUpload sessionId={sessionId} onUploadSuccess={handleUploadSuccess} />

        <QueryInput
          sessionId={sessionId}
          onResult={handleResult}
          disabled={!sessionId}
        />

        {!sessionId && !latestResult && (
          <div className="empty-state-box">
            <div className="empty-icon">📤</div>
            <h3>Upload a document to get started</h3>
            <p>Drop a PDF, DOCX, or TXT file above, then ask for quizzes, flashcards, or summaries.</p>
          </div>
        )}

        {latestResult && (
          <div className="results">
            <div className="result-card">
              <div className="result-intent-badge">
                {latestResult.intent === "quiz" && "🧪 Quiz"}
                {latestResult.intent === "flashcard" && "🃏 Flashcards"}
                {latestResult.intent === "review" && "📋 Review"}
              </div>
              <ResultView result={latestResult} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
