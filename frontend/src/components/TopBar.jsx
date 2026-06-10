import { LogOut, ShieldCheck } from "lucide-react";

export default function TopBar({ user, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">TechKraft</p>
        <h1>Candidate Review</h1>
      </div>
      <div className="topbar-actions">
        <span className="role-pill">
          <ShieldCheck size={16} aria-hidden="true" />
          {user.role}
        </span>
        <span className="user-email">{user.email}</span>
        <button className="icon-button" onClick={onLogout} title="Sign out" aria-label="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
