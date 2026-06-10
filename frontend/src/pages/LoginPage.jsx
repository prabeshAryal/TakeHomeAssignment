import { LockKeyhole, UserPlus } from "lucide-react";
import { useState } from "react";

export default function LoginPage({ onLogin, onRegister }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await onLogin({ email, password });
      } else {
        await onRegister({ email, password });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div className="auth-brand">
          <p className="eyebrow">TechKraft Internal Products</p>
          <h1>Candidate Review</h1>
        </div>

        <div className="segmented" role="tablist" aria-label="Authentication mode">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Login
          </button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Register
          </button>
        </div>

        <form className="form-stack" onSubmit={submit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
          </label>
          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              minLength={8}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="primary-button" disabled={busy}>
            {mode === "login" ? <LockKeyhole size={18} /> : <UserPlus size={18} />}
            {busy ? "Working..." : mode === "login" ? "Login" : "Register"}
          </button>
        </form>

      </section>
    </main>
  );
}
