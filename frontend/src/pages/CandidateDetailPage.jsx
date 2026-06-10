import { ArrowLeft, Bot, Save, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import Loading from "../components/Loading";

const categories = ["Technical depth", "Communication", "Product thinking", "Ownership", "Culture fit"];

export default function CandidateDetailPage({ token, user }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summaryBusy, setSummaryBusy] = useState(false);
  const [summaryError, setSummaryError] = useState("");
  const [scoreForm, setScoreForm] = useState({ category: categories[0], score: 4, note: "" });
  const [notes, setNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [archiving, setArchiving] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const response = await api.getCandidate(token, id);
      setCandidate(response);
      setNotes(response.internal_notes || "");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [id, token]);

  useEffect(() => {
    let active = true;
    const abortController = new AbortController();

    async function startListening() {
      const apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      try {
        const response = await fetch(`${apiBaseUrl}/candidates/${id}/stream`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: abortController.signal,
        });

        if (!response.ok) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (active) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventName = "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("event:")) {
              eventName = trimmed.substring(6).trim();
            } else if (trimmed.startsWith("data:")) {
              const dataVal = trimmed.substring(5).trim();
              if (eventName === "scores" && dataVal && active) {
                try {
                  const updatedScores = JSON.parse(dataVal);
                  setCandidate((prev) => {
                    if (!prev) return null;
                    return { ...prev, scores: updatedScores };
                  });
                } catch (e) {
                  console.error("Error parsing streamed scores", e);
                }
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("SSE stream error", err);
        }
      }
    }

    startListening();

    return () => {
      active = false;
      abortController.abort();
    };
  }, [id, token]);

  async function handleArchive() {
    if (!window.confirm("Are you sure you want to archive this candidate?")) {
      return;
    }
    setArchiving(true);
    try {
      await api.deleteCandidate(token, id);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setArchiving(false);
    }
  }

  async function submitScore(event) {
    event.preventDefault();
    try {
      await api.submitScore(token, id, { ...scoreForm, score: Number(scoreForm.score) });
      setScoreForm((current) => ({ ...current, note: "" }));
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function generateSummary() {
    setSummaryBusy(true);
    setSummaryError("");
    try {
      const response = await api.generateSummary(token, id);
      setCandidate((current) => ({ ...current, ai_summary: response.summary }));
    } catch (err) {
      setSummaryError(err.message);
    } finally {
      setSummaryBusy(false);
    }
  }

  async function saveNotes() {
    setSavingNotes(true);
    setError("");
    try {
      const response = await api.updateNotes(token, id, { internal_notes: notes });
      setCandidate(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingNotes(false);
    }
  }

  if (loading) {
    return (
      <main className="content">
        <Loading label="Loading candidate" />
      </main>
    );
  }

  if (error && !candidate) {
    return (
      <main className="content">
        <Link className="back-link" to="/">
          <ArrowLeft size={16} /> Back
        </Link>
        <p className="error">{error}</p>
      </main>
    );
  }

  return (
    <main className="content detail-grid">
      <section className="detail-main">
        <Link className="back-link" to="/">
          <ArrowLeft size={16} /> Back
        </Link>
        {error && <p className="error">{error}</p>}

        <div className="profile-header">
          <div>
            <h2>{candidate.name}</h2>
            <p>{candidate.email}</p>
          </div>
          <span className={`status-badge status-${candidate.status}`}>{candidate.status}</span>
        </div>

        <dl className="profile-grid">
          <div>
            <dt>Role</dt>
            <dd>{candidate.role_applied}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{new Date(candidate.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt>Skills</dt>
            <dd className="tag-list">
              {candidate.skills.map((skill) => (
                <span key={skill}>{skill}</span>
              ))}
            </dd>
          </div>
        </dl>

        <section className="panel">
          <div className="section-heading">
            <h3>AI Summary</h3>
            <button className="secondary-button" onClick={generateSummary} disabled={summaryBusy}>
              <Bot size={18} />
              {summaryBusy ? "Generating..." : "Generate"}
            </button>
          </div>
          {summaryBusy && <Loading label="Generating mock AI summary" />}
          {summaryError && <p className="error">{summaryError}</p>}
          {!summaryBusy && <p className="summary-text">{candidate.ai_summary || "No summary generated yet."}</p>}
        </section>

        <section className="panel">
          <h3>Scores</h3>
          <div className="score-list">
            {candidate.scores.map((score) => (
              <article className="score-row" key={score.id}>
                <div>
                  <strong>{score.category}</strong>
                  <span>{score.reviewer_email || score.reviewer_id}</span>
                </div>
                <meter min="1" max="5" value={score.score} />
                <b>{score.score}/5</b>
                <p>{score.note || "No note"}</p>
              </article>
            ))}
            {candidate.scores.length === 0 && <p className="empty">No visible scores yet.</p>}
          </div>
        </section>
      </section>

      <aside className="detail-side">
        <section className="panel">
          <h3>Submit Score</h3>
          <form className="form-stack" onSubmit={submitScore}>
            <label>
              Category
              <select value={scoreForm.category} onChange={(event) => setScoreForm({ ...scoreForm, category: event.target.value })}>
                {categories.map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>
            <label>
              Score
              <input
                type="number"
                min="1"
                max="5"
                value={scoreForm.score}
                onChange={(event) => setScoreForm({ ...scoreForm, score: event.target.value })}
              />
            </label>
            <label>
              Note
              <textarea
                rows="5"
                value={scoreForm.note}
                onChange={(event) => setScoreForm({ ...scoreForm, note: event.target.value })}
              />
            </label>
            <button className="primary-button">
              <Send size={18} />
              Submit
            </button>
          </form>
        </section>

        {user.role === "admin" && (
          <section className="panel">
            <h3>Internal Notes</h3>
            <textarea rows="8" value={notes} onChange={(event) => setNotes(event.target.value)} />
            <button className="secondary-button full-width" onClick={saveNotes} disabled={savingNotes}>
              <Save size={18} />
              {savingNotes ? "Saving..." : "Save notes"}
            </button>
            <button
              className="secondary-button full-width"
              onClick={handleArchive}
              disabled={archiving}
              style={{ marginTop: "12px", borderColor: "#ef4444", color: "#ef4444" }}
            >
              Archive Candidate
            </button>
          </section>
        )}
      </aside>
    </main>
  );
}
