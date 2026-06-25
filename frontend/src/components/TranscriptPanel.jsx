import React, { useEffect, useRef } from "react";

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function TranscriptPanel({ transcript }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  return (
    <div className="panel transcript-panel">
      <div className="panel-header">
        <span className="panel-icon">💬</span>
        <h3>Conversation</h3>
        <span className="panel-badge">{transcript.length}</span>
      </div>
      <div className="transcript-body">
        {transcript.length === 0 ? (
          <p className="empty-state">No conversation yet. Start a call to begin.</p>
        ) : (
          transcript.map((msg, idx) => (
            <div key={idx} className={`transcript-msg msg-${msg.role}`}>
              <div className="msg-meta">
                <span className="msg-role">{msg.role === "user" ? "You" : "Assistant"}</span>
                <span className="msg-time">{formatTime(msg.ts)}</span>
              </div>
              <div className="msg-text">{msg.text}</div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
