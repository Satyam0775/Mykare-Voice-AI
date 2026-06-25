import React from 'react';

const TOOL_META = {
  identify_user: { icon: '👤', label: 'Identify Patient', color: '#8b5cf6' },
  fetch_slots: { icon: '📅', label: 'Fetching Slots', color: '#0ea5e9' },
  book_appointment: { icon: '✅', label: 'Book Appointment', color: '#10b981' },
  retrieve_appointments: { icon: '📋', label: 'Retrieve Appointments', color: '#0ea5e9' },
  cancel_appointment: { icon: '❌', label: 'Cancel Appointment', color: '#f43f5e' },
  modify_appointment: { icon: '✏️', label: 'Modify Appointment', color: '#f59e0b' },
  end_conversation: { icon: '👋', label: 'End Conversation', color: '#94a3b8' },
};

function ToolItem({ item }) {
  const meta = TOOL_META[item.toolName] || { icon: '⚙️', label: item.toolName, color: '#94a3b8' };
  const isRunning = item.status === 'running';
  const isComplete = item.status === 'completed';

  const formatDetails = (details) => {
    if (!details) return null;
    if (typeof details === 'string') return details;
    const keys = Object.keys(details).filter(k => details[k] != null);
    if (keys.length === 0) return null;
    const important = ['message', 'appointment_date', 'appointment_time', 'doctor_name', 'available_slots', 'total'];
    const toShow = keys.filter(k => important.includes(k)).slice(0, 3);
    if (toShow.length === 0) return null;
    return toShow.map(k => {
      let val = details[k];
      if (Array.isArray(val)) val = val.slice(0, 3).join(', ') + (val.length > 3 ? '…' : '');
      if (typeof val === 'object') val = JSON.stringify(val).slice(0, 60);
      return `${k}: ${val}`;
    }).join(' · ');
  };

  const detail = formatDetails(item.details);
  const time = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '10px 12px',
        borderRadius: 'var(--radius)',
        background: 'rgba(14, 165, 233, 0.04)',
        border: `1px solid ${isRunning ? meta.color + '40' : 'var(--border)'}`,
        animation: 'tool-flash 0.4s ease forwards',
        opacity: isComplete ? 0.75 : 1,
        transition: 'opacity 0.5s ease',
      }}
    >
      {/* Status indicator */}
      <div style={{
        flexShrink: 0,
        width: 28,
        height: 28,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `${meta.color}18`,
        border: `1px solid ${meta.color}30`,
        fontSize: '14px',
      }}>
        {isRunning ? (
          <div style={{
            width: 12,
            height: 12,
            border: `2px solid ${meta.color}40`,
            borderTop: `2px solid ${meta.color}`,
            borderRadius: '50%',
            animation: 'spin-slow 0.8s linear infinite',
          }} />
        ) : (
          <span>{meta.icon}</span>
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          marginBottom: detail ? '3px' : 0,
        }}>
          <span style={{
            fontSize: '12px',
            fontWeight: 600,
            fontFamily: 'var(--font-display)',
            color: isRunning ? meta.color : 'var(--text-primary)',
            letterSpacing: '0.02em',
          }}>
            {meta.label}
          </span>
          <span style={{
            fontSize: '10px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)',
            flexShrink: 0,
          }}>
            {time}
          </span>
        </div>

        {isRunning && (
          <div style={{
            fontSize: '11px',
            color: meta.color,
            fontFamily: 'var(--font-body)',
          }}>
            Running…
          </div>
        )}

        {isComplete && detail && (
          <div style={{
            fontSize: '11px',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-body)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {detail}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ToolStatus({ activities }) {
  if (!activities || activities.length === 0) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: '10px',
        color: 'var(--text-muted)',
        fontSize: '13px',
        fontFamily: 'var(--font-body)',
      }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
        </svg>
        <span>Tool activity will appear here</span>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '6px',
      flex: 1,
      overflowY: 'auto',
    }}>
      {activities.map(item => (
        <ToolItem key={item.id} item={item} />
      ))}
    </div>
  );
}
