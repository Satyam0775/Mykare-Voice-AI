import React from "react";

const TOOL_ICONS = {
  identify_user: "👤",
  fetch_slots: "📅",
  book_appointment: "✅",
  retrieve_appointments: "📋",
  modify_appointment: "✏️",
  cancel_appointment: "❌",
  end_conversation: "🏁",
};

const STATUS_CLASS = {
  running: "status-running",
  success: "status-success",
  error: "status-error",
};

export default function ToolActivityPanel({ toolEvents }) {
  return (
    <div className="panel tool-panel">
      <div className="panel-header">
        <span className="panel-icon">⚙️</span>
        <h3>Tool Activity</h3>
        {toolEvents.some((e) => e.status === "running") && (
          <span className="live-badge">LIVE</span>
        )}
      </div>
      <div className="tool-body">
        {toolEvents.length === 0 ? (
          <p className="empty-state">Tool calls will appear here during the call.</p>
        ) : (
          toolEvents.map((evt, idx) => (
            <div key={idx} className={`tool-event ${STATUS_CLASS[evt.status] || ""}`}>
              <span className="tool-icon">{TOOL_ICONS[evt.tool] || "🔧"}</span>
              <div className="tool-info">
                <span className="tool-name">{formatToolName(evt.tool)}</span>
                <span className="tool-message">{evt.message}</span>
              </div>
              <span className={`tool-status-dot dot-${evt.status}`} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function formatToolName(tool) {
  return tool
    ? tool
        .split("_")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ")
    : "Unknown";
}
