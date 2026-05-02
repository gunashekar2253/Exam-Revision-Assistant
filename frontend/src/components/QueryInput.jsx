import { useState } from "react";

export default function QueryInput({ sessionId, onResult, disabled }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !sessionId) return;

    setLoading(true);
    setError("");

    try {
      const { sendQuery } = await import("../api");
      const result = await sendQuery(query.trim(), sessionId);
      onResult(result);
      setQuery("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <div className="query-input-wrap">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            disabled
              ? "Upload a document first..."
              : "Ask anything — quiz me, make flashcards, summarize..."
          }
          disabled={disabled || loading}
        />
        <button type="submit" disabled={disabled || loading || !query.trim()}>
          {loading ? "..." : "→"}
        </button>
      </div>
      {error && <div className="error-msg">{error}</div>}
      {!disabled && (
        <div className="query-hints">
          <span onClick={() => setQuery("Generate a quiz")}>🧪 Quiz</span>
          <span onClick={() => setQuery("Create flashcards")}>🃏 Flashcards</span>
          <span onClick={() => setQuery("Give me a summary and study plan")}>📝 Review</span>
        </div>
      )}
    </form>
  );
}
