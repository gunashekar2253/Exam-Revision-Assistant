import { useState } from "react";

export default function FlashcardView({ data }) {
  const cards = data?.cards || data?.data?.cards || [];
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!cards.length) {
    return <div className="empty-state">No flashcards generated.</div>;
  }

  const card = cards[current];

  const next = () => {
    setFlipped(false);
    setCurrent((prev) => (prev + 1) % cards.length);
  };

  const prev = () => {
    setFlipped(false);
    setCurrent((prev) => (prev - 1 + cards.length) % cards.length);
  };

  return (
    <div className="flashcard-view">
      <div className="result-header">
        <h3>🃏 Flashcards ({cards.length} cards)</h3>
        <span className="card-counter">
          {current + 1} / {cards.length}
        </span>
      </div>

      <div
        className={`flashcard ${flipped ? "flipped" : ""}`}
        onClick={() => setFlipped(!flipped)}
      >
        <div className="flashcard-inner">
          <div className="flashcard-front">
            <p>{card.front}</p>
            <span className="flip-hint">Click to flip</span>
          </div>
          <div className="flashcard-back">
            <p>{card.back}</p>
            {card.category && (
              <span className="card-category">{card.category}</span>
            )}
          </div>
        </div>
      </div>

      <div className="flashcard-nav">
        <button className="btn" onClick={prev}>← Prev</button>
        <div className="dot-indicators">
          {cards.map((_, i) => (
            <span
              key={i}
              className={`dot ${i === current ? "active" : ""}`}
              onClick={() => { setCurrent(i); setFlipped(false); }}
            />
          ))}
        </div>
        <button className="btn" onClick={next}>Next →</button>
      </div>
    </div>
  );
}
