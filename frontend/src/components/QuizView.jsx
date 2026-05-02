import { useState } from "react";

export default function QuizView({ data }) {
  const questions = data?.questions || data?.data?.questions || [];
  const [selected, setSelected] = useState({});
  const [showAnswers, setShowAnswers] = useState(false);

  if (!questions.length) {
    return <div className="empty-state">No quiz questions generated.</div>;
  }

  const handleSelect = (qIdx, option) => {
    if (showAnswers) return;
    setSelected((prev) => ({ ...prev, [qIdx]: option }));
  };

  const score = Object.entries(selected).filter(
    ([idx, ans]) => ans === questions[idx]?.correct_answer
  ).length;

  return (
    <div className="quiz-view">
      <div className="result-header">
        <h3>📝 Quiz ({questions.length} questions)</h3>
        {showAnswers && (
          <div className="score">
            Score: {score}/{questions.length}
          </div>
        )}
      </div>

      {questions.map((q, idx) => {
        const options = q.options || {};
        const isCorrect = selected[idx] === q.correct_answer;

        return (
          <div key={idx} className="quiz-question">
            <p className="q-text">
              <strong>Q{idx + 1}.</strong> {q.question}
            </p>
            {q.difficulty && (
              <span className={`difficulty ${q.difficulty}`}>{q.difficulty}</span>
            )}
            <div className="options">
              {Object.entries(options).map(([key, value]) => {
                let cls = "option";
                if (showAnswers) {
                  if (key === q.correct_answer) cls += " correct";
                  else if (key === selected[idx]) cls += " wrong";
                } else if (selected[idx] === key) {
                  cls += " selected";
                }

                return (
                  <button
                    key={key}
                    className={cls}
                    onClick={() => handleSelect(idx, key)}
                  >
                    <span className="option-key">{key}</span>
                    {value}
                  </button>
                );
              })}
            </div>
            {showAnswers && q.explanation && (
              <p className="explanation">💡 {q.explanation}</p>
            )}
          </div>
        );
      })}

      <div className="quiz-actions">
        {!showAnswers ? (
          <button
            className="btn primary"
            onClick={() => setShowAnswers(true)}
            disabled={Object.keys(selected).length === 0}
          >
            Check Answers
          </button>
        ) : (
          <button
            className="btn"
            onClick={() => {
              setSelected({});
              setShowAnswers(false);
            }}
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
