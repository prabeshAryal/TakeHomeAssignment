const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { token, ...options } = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(data.detail || "Request failed", response.status);
  }

  return data;
}

export const api = {
  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listCandidates: (token, params) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        query.set(key, value);
      }
    });
    return request(`/candidates?${query.toString()}`, { token });
  },
  getCandidate: (token, id) => request(`/candidates/${id}`, { token }),
  submitScore: (token, id, payload) =>
    request(`/candidates/${id}/scores`, {
      token,
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateSummary: (token, id) =>
    request(`/candidates/${id}/summary`, {
      token,
      method: "POST",
    }),
  updateNotes: (token, id, payload) =>
    request(`/candidates/${id}/notes`, {
      token,
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteCandidate: (token, id) =>
    request(`/candidates/${id}`, {
      token,
      method: "DELETE",
    }),
};

