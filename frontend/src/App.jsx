import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "./api/client";
import TopBar from "./components/TopBar";
import CandidateDetailPage from "./pages/CandidateDetailPage";
import CandidateListPage from "./pages/CandidateListPage";
import LoginPage from "./pages/LoginPage";

const storedSession = () => {
  try {
    return JSON.parse(localStorage.getItem("techkraft-session") || "null");
  } catch {
    return null;
  }
};

export default function App() {
  const [session, setSession] = useState(storedSession);
  const navigate = useNavigate();

  useEffect(() => {
    if (session) {
      localStorage.setItem("techkraft-session", JSON.stringify(session));
    } else {
      localStorage.removeItem("techkraft-session");
    }
  }, [session]);

  async function login(payload) {
    const response = await api.login(payload);
    setSession(response);
    navigate("/");
  }

  async function register(payload) {
    const response = await api.register(payload);
    setSession(response);
    navigate("/");
  }

  function logout() {
    setSession(null);
    navigate("/login");
  }

  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={login} onRegister={register} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <TopBar user={session.user} onLogout={logout} />
      <Routes>
        <Route path="/" element={<CandidateListPage token={session.access_token} />} />
        <Route
          path="/candidates/:id"
          element={<CandidateDetailPage token={session.access_token} user={session.user} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
