import React from "react";

export default function SummaryPanel({ summary }) {
  if (!summary) {
    return (
      <div className="panel summary-panel">
        <div className="panel-header">
          <span className="panel-icon">📝</span>
          <h3>Call Summary</h3>
        </div>
        <p className="empty-state">Summary will appear after the call ends.</p>
      </div>
    );
  }

  return (
    <div className="panel summary-panel summary-filled">
      <div className="panel-header">
        <span className="panel-icon">📝</span>
        <h3>Call Summary</h3>
        <span className="summary-time">{new Date(summary.timestamp || Date.now()).toLocaleString()}</span>
      </div>

      <div className="summary-body">
        {/* Patient info */}
        <div className="summary-section">
          <h4>Patient</h4>
          <div className="summary-kv">
            {summary.user_name && <SummaryRow label="Name" value={summary.user_name} />}
            {summary.user_phone && <SummaryRow label="Phone" value={summary.user_phone} />}
          </div>
        </div>

        {/* Conversation summary text */}
        {summary.summary && (
          <div className="summary-section">
            <h4>Conversation Summary</h4>
            <p className="summary-text">{summary.summary}</p>
          </div>
        )}

        {/* Appointments */}
        {summary.appointments && summary.appointments.length > 0 && (
          <div className="summary-section">
            <h4>Appointments</h4>
            {summary.appointments.map((a, i) => (
              <div key={i} className="summary-appt">
                <span>{a.date} @ {a.time}</span>
                <span className="appt-tag">{a.status}</span>
              </div>
            ))}
          </div>
        )}

        {/* Intent */}
        {summary.intent && (
          <div className="summary-section">
            <h4>Primary Intent</h4>
            <p className="summary-intent">{summary.intent}</p>
          </div>
        )}

        {/* Preferences */}
        {summary.preferences && (
          <div className="summary-section">
            <h4>Preferences</h4>
            <p className="summary-text">{summary.preferences}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="summary-row">
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  );
}
