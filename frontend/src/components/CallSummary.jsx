import React, { useState, useEffect } from 'react';
import { generateSummary } from '../services/api.js';

function AppointmentCard({ appt }) {
  const statusColor = {
    confirmed: 'var(--emerald)',
    cancelled: 'var(--rose)',
    completed: 'var(--text-muted)',
  }[appt.status] || 'var(--text-secondary)';

  return (
    <div style={{
      padding: '12px 14px',
      borderRadius: 'var(--radius)',
      background: 'rgba(16, 185, 129, 0.06)',
      border: '1px solid rgba(16, 185, 129, 0.15)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: '12px',
    }}>
      <div>
        <div style={{
          fontSize: '13px',
          fontWeight: 600,
          fontFamily: 'var(--font-display)',
          color: 'var(--text-primary)',
          marginBottom: '4px',
        }}>
          {appt.appointment_date} at {appt.appointment_time}
        </div>
        <div style={{
          fontSize: '12px',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-body)',
        }}>
          {appt.doctor_name} · {appt.department}
        </div>
        {appt.reason && (
          <div style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)',
            marginTop: '3px',
          }}>
            {appt.reason}
          </div>
        )}
      </div>
      <span style={{
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        color: statusColor,
        flexShrink: 0,
        fontFamily: 'var(--font-display)',
      }}>
        {appt.status}
      </span>
    </div>
  );
}

export default function CallSummary({ transcript, onClose, isVisible }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isVisible || transcript.length === 0) return;
    setLoading(true);
    setError(null);

    const messages = transcript
      .filter(m => m.role !== 'system')
      .map(m => ({ role: m.role, content: m.content }));

    generateSummary(messages)
      .then(data => {
        setSummary(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        background: 'rgba(6, 13, 26, 0.85)',
        backdropFilter: 'blur(8px)',
        animation: 'fade-up 0.3s ease both',
      }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          maxHeight: '80vh',
          overflowY: 'auto',
          borderRadius: 'var(--radius-xl)',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-bright)',
          boxShadow: 'var(--shadow-glow)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '24px 24px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '4px',
            }}>
              Call Summary
            </h2>
            <p style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-body)',
            }}>
              {new Date().toLocaleString()}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              border: '1px solid var(--border)',
              background: 'transparent',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'var(--transition)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loading && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
              padding: '32px 0',
              color: 'var(--text-muted)',
            }}>
              <div style={{
                width: 32,
                height: 32,
                border: '3px solid var(--border)',
                borderTop: '3px solid var(--cyan)',
                borderRadius: '50%',
                animation: 'spin-slow 0.8s linear infinite',
              }} />
              <span style={{ fontSize: '13px', fontFamily: 'var(--font-body)' }}>
                Generating summary…
              </span>
            </div>
          )}

          {error && (
            <div style={{
              padding: '12px 14px',
              borderRadius: 'var(--radius)',
              background: 'rgba(244, 63, 94, 0.08)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              fontSize: '13px',
              color: 'var(--rose)',
              fontFamily: 'var(--font-body)',
            }}>
              Failed to generate summary: {error}
            </div>
          )}

          {summary && !loading && (
            <>
              {/* Overview */}
              {summary.summary && (
                <div>
                  <h3 style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--cyan)',
                    fontFamily: 'var(--font-display)',
                    marginBottom: '10px',
                  }}>
                    Overview
                  </h3>
                  <p style={{
                    fontSize: '13px',
                    lineHeight: 1.65,
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-body)',
                  }}>
                    {summary.summary}
                  </p>
                </div>
              )}

              {/* Key Points */}
              {summary.key_points && summary.key_points.length > 0 && (
                <div>
                  <h3 style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--cyan)',
                    fontFamily: 'var(--font-display)',
                    marginBottom: '10px',
                  }}>
                    Key Actions
                  </h3>
                  <ul style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                    listStyle: 'none',
                  }}>
                    {summary.key_points.map((pt, i) => (
                      <li
                        key={i}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '8px',
                          fontSize: '13px',
                          color: 'var(--text-secondary)',
                          fontFamily: 'var(--font-body)',
                        }}
                      >
                        <span style={{ color: 'var(--teal)', flexShrink: 0, marginTop: '2px' }}>▸</span>
                        {pt}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Appointments */}
              {summary.appointments && summary.appointments.length > 0 && (
                <div>
                  <h3 style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--cyan)',
                    fontFamily: 'var(--font-display)',
                    marginBottom: '10px',
                  }}>
                    Appointments
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {summary.appointments.map((a, i) => (
                      <AppointmentCard key={i} appt={a} />
                    ))}
                  </div>
                </div>
              )}

              {/* User Preferences */}
              {summary.user_preferences && (
                Array.isArray(summary.user_preferences)
                  ? summary.user_preferences.length > 0
                  : !!summary.user_preferences
              ) && (
                <div>
                  <h3 style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--cyan)',
                    fontFamily: 'var(--font-display)',
                    marginBottom: '10px',
                  }}>
                    Patient Preferences
                  </h3>
                  <div style={{
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-body)',
                  }}>
                    {Array.isArray(summary.user_preferences)
                      ? summary.user_preferences.join(', ')
                      : summary.user_preferences}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Transcript count */}
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius)',
            background: 'var(--bg-hover)',
            border: '1px solid var(--border)',
            fontSize: '12px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)',
            display: 'flex',
            justifyContent: 'space-between',
          }}>
            <span>Transcript messages</span>
            <span style={{ color: 'var(--text-secondary)' }}>{transcript.filter(m => m.role !== 'system').length}</span>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'flex-end',
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 20px',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border-bright)',
              background: 'linear-gradient(135deg, rgba(14,165,233,0.15), rgba(14,165,233,0.05))',
              color: 'var(--cyan)',
              fontFamily: 'var(--font-display)',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              letterSpacing: '0.04em',
              transition: 'var(--transition)',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
