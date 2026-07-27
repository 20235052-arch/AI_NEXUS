// src/components/AnatomyPanel.jsx
//
// STEP 5: Interact — click on the organ and ask questions.
// Appears once a structure has been clicked (structure prop is non-null).
// Shows the default AI explanation immediately, plus a text box so the
// user can ask a follow-up question about that structure.

import { useEffect, useState } from "react";
import { getAnatomyInfo, askQuestion } from "../api";

export default function AnatomyPanel({ structure }) {
  const [info, setInfo] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    if (!structure) return;
    setInfo(null);
    setAnswer(null);
    getAnatomyInfo(structure).then(setInfo);
  }, [structure]);

  if (!structure) {
    return (
      <div className="panel anatomy-panel empty">
        <p className="subtitle">Click the organ in the 3D view to learn more about it.</p>
      </div>
    );
  }

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const result = await askQuestion(structure, question);
      setAnswer(result.answer);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="panel anatomy-panel">
      {!info ? (
        <p>Loading explanation...</p>
      ) : (
        <>
          <h3>{info.display_name}</h3>
          <p>{info.what_it_is}</p>

          <p className="label-small">Function</p>
          <p>{info.function}</p>

          <p className="label-small">Neighboring Structures</p>
          <div className="chip-row">
            {info.neighboring_structures.map((s) => (
              <span className="chip" key={s}>{s}</span>
            ))}
          </div>
        </>
      )}

      <div className="ask-box">
        <input
          type="text"
          placeholder={`Ask a question about the ${structure}...`}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
        />
        <button onClick={handleAsk} disabled={asking}>
          {asking ? "Thinking..." : "Ask"}
        </button>
      </div>

      {answer && <p className="answer-text">{answer}</p>}
    </div>
  );
}
