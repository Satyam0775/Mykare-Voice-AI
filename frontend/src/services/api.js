import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: BASE, timeout: 15000 });

// ── Token ─────────────────────────────────────────────────────────────────
export async function fetchToken(roomName, participantName) {
  const { data } = await api.post("/api/calls/token", { room_name: roomName, participant_name: participantName });
  return data; // { token, room_name, livekit_url }
}

// ── Start call ────────────────────────────────────────────────────────────
export async function startCall(roomName, userPhone = null) {
  const { data } = await api.post("/api/calls/start", { room_name: roomName, user_phone: userPhone });
  return data;
}

// ── Appointments ──────────────────────────────────────────────────────────
export async function getAppointments(userPhone) {
  const { data } = await api.get(`/api/appointments/${userPhone}`);
  return data;
}

// ── Session summary ───────────────────────────────────────────────────────
export async function getSessionSummary(sessionId) {
  const { data } = await api.get(`/api/sessions/${sessionId}/summary`);
  return data;
}

// ── Available slots ───────────────────────────────────────────────────────
export async function getSlots() {
  const { data } = await api.get("/api/slots");
  return data;
}

// ── Health check ──────────────────────────────────────────────────────────
export async function healthCheck() {
  const { data } = await api.get("/api/health");
  return data;
}

export default api;
