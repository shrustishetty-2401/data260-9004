import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8004",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function login(username, password) {
  const response = await api.post("/auth/login", {
    username,
    password,
  });

  localStorage.setItem(
    "access_token",
    response.data.access_token,
  );

  return response.data.user;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me");
  return response.data;
}

export function logout() {
  localStorage.removeItem("access_token");
}

export async function getReports(skip = 0, limit = 10) {
  const response = await api.get("/api/reports", {
    params: { skip, limit },
  });

  return response.data;
}

export async function createReport(payload) {
  const response = await api.post("/api/reports", payload);
  return response.data;
}

export async function updateReport(id, payload) {
  const response = await api.put(
    `/api/reports/${id}`,
    payload,
  );

  return response.data;
}

export async function deleteReport(id) {
  const response = await api.delete(
    `/api/reports/${id}`,
  );

  return response.data;
}