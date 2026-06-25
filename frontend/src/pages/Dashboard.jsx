import React from "react";
import { useVoiceAgent } from "../hooks/useVoiceAgent.js";
import Avatar from "../components/Avatar.jsx";
import VoiceControls from "../components/VoiceControls.jsx";
import TranscriptPanel from "../components/TranscriptPanel.jsx";
import ToolActivityPanel from "../components/ToolActivityPanel.jsx";
import AppointmentPanel from "../components/AppointmentPanel.jsx";
import SummaryPanel from "../components/SummaryPanel.jsx";

export default function Dashboard() {
  const {
    callStatus,
    transcript,
    toolEvents,
    appointments,
    summary,
    error,
    isSpeaking,
    isListening,
    localMuted,
    connectionState,
    startVoiceCall,
    endVoiceCall,
    toggleMute,
  } = useVoiceAgent();

  return (
    <div className="dashboard">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="dashboard-header">
        <div className="header-brand">
          <span className="brand-icon">🏥</span>
          <span className="brand-name">Mykare</span>
          <span className="brand-sub">Voice AI Assistant</span>
        </div>
        <div className="header-status">
          <span className={`call-status-badge badge-${callStatus}`}>
            {callStatus.charAt(0).toUpperCase() + callStatus.slice(1)}
          </span>
        </div>
      </header>

      {/* ── Main grid ──────────────────────────────────────────────── */}
      <main className="dashboard-grid">

        {/* Left column — avatar + controls */}
        <aside className="col-left">
          <Avatar isSpeaking={isSpeaking} isListening={isListening && callStatus === "active"} />
          <VoiceControls
            callStatus={callStatus}
            localMuted={localMuted}
            connectionState={connectionState}
            onStart={startVoiceCall}
            onEnd={endVoiceCall}
            onToggleMute={toggleMute}
            error={error}
          />
        </aside>

        {/* Center column — transcript */}
        <section className="col-center">
          <TranscriptPanel transcript={transcript} />
        </section>

        {/* Right column — tool feed + appointments + summary */}
        <aside className="col-right">
          <ToolActivityPanel toolEvents={toolEvents} />
          <AppointmentPanel appointments={appointments} />
          <SummaryPanel summary={summary} />
        </aside>

      </main>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="dashboard-footer">
        <span>Powered by LiveKit · Deepgram · Cartesia · OpenRouter</span>
      </footer>
    </div>
  );
}
