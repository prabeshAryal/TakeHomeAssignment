import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import Loading from "../components/Loading";

const statuses = ["", "new", "reviewed", "hired", "rejected", "archived"];

export default function CandidateListPage({ token }) {
  const [filters, setFilters] = useState({
    status: "",
    role_applied: "",
    skill: "",
    keyword: "",
  });
  const [page, setPage] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const limit = 10;

  const params = useMemo(
    () => ({
      ...filters,
      offset: page * limit,
      limit,
    }),
    [filters, page]
  );

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    api
      .listCandidates(token, params)
      .then((response) => {
        if (alive) setData(response);
      })
      .catch((err) => {
        if (alive) setError(err.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [token, params]);

  function updateFilter(name, value) {
    setPage(0);
    setFilters((current) => ({ ...current, [name]: value }));
  }

  const total = data?.total ?? 0;
  const canPrev = page > 0;
  const canNext = (page + 1) * limit < total;

  return (
    <main className="content">
      <section className="toolbar">
        <label className="search-field">
          <Search size={18} />
          <input
            placeholder="Search name, email, role, skill"
            value={filters.keyword}
            onChange={(event) => updateFilter("keyword", event.target.value)}
          />
        </label>
        <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
          {statuses.map((status) => (
            <option value={status} key={status || "all"}>
              {status || "All statuses"}
            </option>
          ))}
        </select>
        <input
          value={filters.role_applied}
          onChange={(event) => updateFilter("role_applied", event.target.value)}
          placeholder="Role"
        />
        <input value={filters.skill} onChange={(event) => updateFilter("skill", event.target.value)} placeholder="Skill" />
      </section>

      {error && <p className="error">{error}</p>}
      {loading && <Loading label="Loading candidates" />}

      {!loading && data && (
        <section className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Skills</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((candidate) => (
                <tr key={candidate.id}>
                  <td>
                    <Link to={`/candidates/${candidate.id}`} className="candidate-link">
                      {candidate.name}
                      <span>{candidate.email}</span>
                    </Link>
                  </td>
                  <td>{candidate.role_applied}</td>
                  <td>
                    <span className={`status-badge status-${candidate.status}`}>{candidate.status}</span>
                  </td>
                  <td>
                    <div className="tag-list">
                      {candidate.skills.map((skill) => (
                        <span key={skill}>{skill}</span>
                      ))}
                    </div>
                  </td>
                  <td>{new Date(candidate.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.items.length === 0 && <p className="empty">No candidates match these filters.</p>}
        </section>
      )}

      <footer className="pagination">
        <span>
          {total === 0 ? "0" : page * limit + 1}-{Math.min((page + 1) * limit, total)} of {total}
        </span>
        <div>
          <button className="icon-button" onClick={() => setPage((value) => value - 1)} disabled={!canPrev} title="Previous">
            <ChevronLeft size={18} />
          </button>
          <button className="icon-button" onClick={() => setPage((value) => value + 1)} disabled={!canNext} title="Next">
            <ChevronRight size={18} />
          </button>
        </div>
      </footer>
    </main>
  );
}
