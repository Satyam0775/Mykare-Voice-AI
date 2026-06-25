import React, { useEffect, useRef, useState } from "react";

const BP_AGENT_ID = import.meta.env.VITE_BP_AGENT_ID || "";

/**
 * Avatar component.
 *
 * If VITE_BP_AGENT_ID is set, renders a Beyond Presence iframe.
 * Otherwise shows an animated SVG avatar that reacts to speaking/listening state.
 */
export default function Avatar({ isSpeaking, isListening }) {
  const state = isSpeaking ? "speaking" : isListening ? "listening" : "idle";

  if (BP_AGENT_ID) {
    return <BeyondPresenceAvatar agentId={BP_AGENT_ID} isSpeaking={isSpeaking} />;
  }
  return <AnimatedAvatar state={state} />;
}

// ── Beyond Presence iframe integration ─────────────────────────────────────
function BeyondPresenceAvatar({ agentId, isSpeaking }) {
  const iframeRef = useRef(null);

  useEffect(() => {
    if (!iframeRef.current) return;
    try {
      iframeRef.current.contentWindow?.postMessage(
        { type: isSpeaking ? "speak" : "idle" },
        "*"
      );
    } catch (_) {}
  }, [isSpeaking]);

  return (
    <div className="avatar-container">
      <iframe
        ref={iframeRef}
        src={`https://app.beyondpresence.ai/embed/${agentId}`}
        title="Beyond Presence Avatar"
        allow="camera; microphone; autoplay"
        className="bp-iframe"
      />
    </div>
  );
}

// ── Animated SVG fallback avatar ────────────────────────────────────────────
function AnimatedAvatar({ state }) {
  const label = state === "speaking" ? "Speaking…" : state === "listening" ? "Listening…" : "Idle";

  return (
    <div className={`avatar-container avatar-${state}`}>
      <div className="avatar-glow" />
      <svg viewBox="0 0 200 200" className="avatar-svg" aria-label={`Avatar — ${label}`}>
        {/* Head */}
        <circle cx="100" cy="80" r="48" fill="#1e6fa8" />
        {/* Face */}
        <ellipse cx="85" cy="76" rx="7" ry="8" fill="white" />
        <ellipse cx="115" cy="76" rx="7" ry="8" fill="white" />
        <ellipse cx="85" cy="77" rx="4" ry="5" fill="#0d4f80" />
        <ellipse cx="115" cy="77" rx="4" ry="5" fill="#0d4f80" />
        {/* Mouth — animates when speaking */}
        {state === "speaking" ? (
          <ellipse cx="100" cy="100" rx="14" ry="7" fill="white" className="mouth-speak">
            <animate attributeName="ry" values="4;9;4;7;4" dur="0.6s" repeatCount="indefinite" />
          </ellipse>
        ) : (
          <path d="M87 100 Q100 108 113 100" stroke="white" strokeWidth="2.5" fill="none" />
        )}
        {/* Body */}
        <rect x="60" y="135" width="80" height="55" rx="16" fill="#1e6fa8" />
        {/* Collar / cross icon */}
        <rect x="97" y="148" width="6" height="24" rx="2" fill="white" opacity="0.8" />
        <rect x="88" y="157" width="24" height="6" rx="2" fill="white" opacity="0.8" />
      </svg>

      {/* Listening pulse rings */}
      {state === "listening" && (
        <div className="pulse-rings">
          <div className="pulse-ring r1" />
          <div className="pulse-ring r2" />
          <div className="pulse-ring r3" />
        </div>
      )}

      {/* Speaking waveform bars */}
      {state === "speaking" && (
        <div className="wave-bars">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className={`wave-bar wb${i}`} />
          ))}
        </div>
      )}

      <p className="avatar-label">{label}</p>
    </div>
  );
}
