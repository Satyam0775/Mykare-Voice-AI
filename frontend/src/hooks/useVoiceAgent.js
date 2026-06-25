import { useState, useCallback, useRef } from "react";
import { useLiveKit } from "./useLiveKit.js";
import { fetchToken, startCall, getSessionSummary } from "../services/api.js";

function generateRoomName() {
  return `mykare-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export function useVoiceAgent() {
  const [callStatus, setCallStatus] = useState("idle"); // idle | connecting | active | ending | ended
  const [transcript, setTranscript] = useState([]); // [{role, text, ts}]
  const [toolEvents, setToolEvents] = useState([]); // [{tool, status, message, ts}]
  const [appointments, setAppointments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [roomName, setRoomName] = useState("");

  const roomNameRef = useRef("");
  const sessionIdRef = useRef("");

  // ── LiveKit data-channel callbacks ────────────────────────────────────────
  const handleTranscript = useCallback((data) => {
    setTranscript((prev) => [
      ...prev,
      { role: data.role || "assistant", text: data.text || "", ts: data.ts || Date.now() },
    ]);
  }, []);

  const handleToolEvent = useCallback((data) => {
    setToolEvents((prev) => [
      { tool: data.tool, status: data.status, message: data.message, ts: Date.now() },
      ...prev.slice(0, 49), // keep last 50
    ]);
  }, []);

  const handleAppointmentUpdate = useCallback((data) => {
    if (Array.isArray(data)) {
      setAppointments(data);
    } else if (data?.appointment) {
      setAppointments((prev) => {
        const idx = prev.findIndex((a) => a.id === data.appointment.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = data.appointment;
          return next;
        }
        return [data.appointment, ...prev];
      });
    }
  }, []);

  const handleSummary = useCallback((data) => {
    setSummary(data);
    setCallStatus("ended");
  }, []);

  const { connect, disconnect, toggleMute, connectionState, isSpeaking, isListening, localMuted } =
    useLiveKit({
      onTranscript: handleTranscript,
      onToolEvent: handleToolEvent,
      onAppointmentUpdate: handleAppointmentUpdate,
      onSummary: handleSummary,
    });

  // ── Start call ─────────────────────────────────────────────────────────────
  const startVoiceCall = useCallback(async () => {
    setError(null);
    setCallStatus("connecting");
    setTranscript([]);
    setToolEvents([]);
    setSummary(null);

    const room = generateRoomName();
    roomNameRef.current = room;
    setRoomName(room);

    try {
      // 1. Get LiveKit JWT from backend
      const { token } = await fetchToken(room, "user");

      // 2. Tell backend to dispatch the agent to this room; capture the session_id
      const callData = await startCall(room);
      if (callData?.session_id) {
        sessionIdRef.current = callData.session_id;
      }

      // 3. Connect to LiveKit
      await connect(token);

      setCallStatus("active");
    } catch (err) {
      console.error("[useVoiceAgent] startVoiceCall error", err);
      setError(err?.response?.data?.detail || err.message || "Failed to start call");
      setCallStatus("idle");
    }
  }, [connect]);

  // ── End call ───────────────────────────────────────────────────────────────
  const endVoiceCall = useCallback(async () => {
    setCallStatus("ending");
    try {
      // Give the agent ~2s to generate summary before disconnecting
      await new Promise((r) => setTimeout(r, 2000));
      // Fetch summary via REST as fallback if WS summary hasn't arrived
      if (!summary && sessionIdRef.current) {
        try {
          const s = await getSessionSummary(sessionIdRef.current);
          if (s) setSummary(s);
        } catch (_) {}
      }
    } finally {
      await disconnect();
      setCallStatus("ended");
    }
  }, [disconnect, summary]);

  return {
    callStatus,
    transcript,
    toolEvents,
    appointments,
    summary,
    error,
    roomName,
    isSpeaking,
    isListening,
    localMuted,
    connectionState,
    startVoiceCall,
    endVoiceCall,
    toggleMute,
  };
}
