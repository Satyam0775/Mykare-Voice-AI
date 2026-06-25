import React from "react";

export default function VoiceControls({
  callStatus,
  localMuted,
  connectionState,
  onStart,
  onEnd,
  onToggleMute,
  error,
}) {
  const isActive = callStatus === "active";
  const isConnecting = callStatus === "connecting";
  const isEnding = callStatus === "ending";
  const isBusy = isConnecting || isEnding;

  return (
    <div className="voice-controls-panel">
      <div className="vc-status-row">
        <span className={`connection-dot dot-${connectionState}`} />
        <span className="connection-label">
          {connectionState === "connected"
            ? "Connected"
            : connectionState === "connecting"
            ? "Connecting…"
            : connectionState === "reconnecting"
            ? "Reconnecting…"
            : "Disconnected"}
        </span>
      </div>

      {error && <div className="vc-error">{error}</div>}

      <div className="vc-buttons">
        {!isActive && !isBusy ? (
          <button
            className="btn btn-start"
            onClick={onStart}
            disabled={callStatus === "ended" && false}
          >
            <span className="btn-icon">📞</span> Start Call
          </button>
        ) : isActive ? (
          <>
            <button
              className={`btn btn-mute ${localMuted ? "btn-muted" : ""}`}
              onClick={onToggleMute}
            >
              {localMuted ? "🔇 Unmute" : "🎙 Mute"}
            </button>
            <button className="btn btn-end" onClick={onEnd} disabled={isEnding}>
              {isEnding ? "Ending…" : "⏹ End Call"}
            </button>
          </>
        ) : (
          <button className="btn btn-start" disabled>
            {isConnecting ? "Connecting…" : "Ending…"}
          </button>
        )}
      </div>

      {callStatus === "ended" && (
        <button className="btn btn-restart" onClick={onStart}>
          🔄 New Call
        </button>
      )}
    </div>
  );
}
