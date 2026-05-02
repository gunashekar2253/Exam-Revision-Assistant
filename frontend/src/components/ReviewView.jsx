export default function ReviewView({ data }) {
  const review = data?.data || data || {};
  const summary = review.summary || "";
  const keyPoints = review.key_points || [];
  const studyPlan = review.study_plan || [];
  const examTopics = review.exam_topics || [];

  if (!summary && !keyPoints.length) {
    return <div className="empty-state">No review content generated.</div>;
  }

  return (
    <div className="review-view">
      <div className="result-header">
        <h3>📋 Study Review</h3>
      </div>

      {summary && (
        <div className="review-section">
          <h4>Summary</h4>
          <p>{summary}</p>
        </div>
      )}

      {keyPoints.length > 0 && (
        <div className="review-section">
          <h4>Key Points</h4>
          <ul>
            {keyPoints.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        </div>
      )}

      {studyPlan.length > 0 && (
        <div className="review-section">
          <h4>Study Plan</h4>
          <div className="study-plan">
            {studyPlan.map((step, i) => (
              <div key={i} className="plan-step">
                <div className="step-number">{step.step || i + 1}</div>
                <div className="step-content">
                  <strong>{step.action}</strong>
                  {step.duration && <span className="step-meta">⏱ {step.duration}</span>}
                  {step.focus && <span className="step-meta">📌 {step.focus}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {examTopics.length > 0 && (
        <div className="review-section">
          <h4>Likely Exam Topics</h4>
          <div className="topic-tags">
            {examTopics.map((topic, i) => (
              <span key={i} className="tag">{topic}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
