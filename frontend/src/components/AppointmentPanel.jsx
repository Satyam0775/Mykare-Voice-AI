import React from "react";

const STATUS_COLORS = {
  confirmed: "#22c55e",
  cancelled: "#ef4444",
  rescheduled: "#f59e0b",
  pending: "#6366f1",
};

export default function AppointmentPanel({ appointments }) {
  return (
    <div className="panel appt-panel">
      <div className="panel-header">
        <span className="panel-icon">📅</span>
        <h3>Appointments</h3>
        <span className="panel-badge">{appointments.length}</span>
      </div>
      <div className="appt-body">
        {appointments.length === 0 ? (
          <p className="empty-state">No appointments yet.</p>
        ) : (
          appointments.map((appt, idx) => (
            <div key={appt.id || idx} className="appt-card">
              <div className="appt-row">
                <span className="appt-date">📆 {appt.date}</span>
                <span className="appt-time">🕐 {appt.time}</span>
              </div>
              <div className="appt-row">
                <span className="appt-phone">📱 {appt.user_phone}</span>
                <span
                  className="appt-status"
                  style={{ color: STATUS_COLORS[appt.status] || "#64748b" }}
                >
                  {appt.status?.toUpperCase()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
