import React, { useEffect, useRef } from 'react';
import { CALL_STATE } from '../hooks/useVoice.js';

export default function VoiceOrb({
  callState,
  isAgentSpeaking,
  isUserSpeaking,
  audioLevel,
  onConnect,
  onDisconnect,
  onMute,
  isMuted,
}) {
  const orbRef = useRef(null);

  const isActive = callState === CALL_STATE.CONNECTED;
  const isConnecting = callState === CALL_STATE.CONNECTING || callState === CALL_STATE.DISCONNECTING;

  const buttonLabel = {
    [CALL_STATE.IDLE]: 'Start Call',
    [CALL_STATE.CONNECTING]: 'Connecting…',
    [CALL_STATE.CONNECTED]: 'End Call',
    [CALL_STATE.DISCONNECTING]: 'Ending…',
    [CALL_STATE.ERROR]: 'Retry',
  }[callState] || 'Start Call';

  const handleClick = () => {
    if (isConnecting) return;
    if (isActive) onDisconnect();
    else onConnect();
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '24px',
    }}>
      {/* Main orb button */}
      <button
        ref={orbRef}
        onClick={handleClick}
        disabled={isConnecting}
        style={{
          position: 'relative',
          width: 96,
          height: 96,
          borderRadius: '50%',
          border: 'none',
          cursor: isConnecting ? 'not-allowed' : 'pointer',
          background: isActive
            ? 'linear-gradient(135deg, #f43f5e, #e11d48)'
            : 'linear-gradient(135deg, #0ea5e9, #0284c7)',
          boxShadow: isActive
            ? '0 0 30px rgba(244, 63, 94, 0.5), 0 0 60px rgba(244, 63, 94, 0.2)'
            : '0 0 30px rgba(14, 165, 233, 0.4), 0 0 60px rgba(14, 165, 233, 0.15)',
          transition: 'all 0.3s ease',
          animation: isActive ? 'glow-pulse 2s ease-in-out infinite' : 'none',
          transform: isConnecting ? 'scale(0.95)' : 'scale(1)',
          outline: 'none',
        }}
        aria-label={buttonLabel}
      >
        {isConnecting ? (
          <div style={{
            width: 28,
            height: 28,
            border: '3px solid rgba(255,255,255,0.3)',
            borderTop: '3px solid white',
            borderRadius: '50%',
            margin: 'auto',
            animation: 'spin-slow 0.8s linear infinite',
          }} />
        ) : isActive ? (
          // Phone hangup icon
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" style={{ margin: 'auto', display: 'block' }}>
            <path d="M16.5 9.4l-2.5 2.5-1.4-1.4L15 8l-1.5-1.5C11.8 7.9 10.1 9 8.6 10.5S6.1 14 6.6 15.7L8 17l-2.5 2.5L3 17C2.5 15.5 3 13 4.7 10.5 6.4 8 9 5.5 11.5 4L16.5 9.4zm1.8-3.6l1.4 1.4-1.4 1.4-1.4-1.4 1.4-1.4z" fill="white"/>
            <path d="M19 5l-7 7-1.5-1.5L18 4l1 1z" fill="white"/>
          </svg>
        ) : (
          // Phone icon
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" style={{ margin: 'auto', display: 'block' }}>
            <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z" fill="white"/>
          </svg>
        )}

        {/* Pulse rings when active */}
        {isActive && (
          <>
            <div style={{
              position: 'absolute',
              inset: -12,
              borderRadius: '50%',
              border: '2px solid rgba(244, 63, 94, 0.4)',
              animation: 'pulse-ring 2s ease-in-out infinite',
              pointerEvents: 'none',
            }} />
            <div style={{
              position: 'absolute',
              inset: -24,
              borderRadius: '50%',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              animation: 'pulse-ring 2s ease-in-out infinite 0.5s',
              pointerEvents: 'none',
            }} />
          </>
        )}
      </button>

      {/* Label */}
      <div style={{
        fontSize: '12px',
        fontFamily: 'var(--font-body)',
        fontWeight: 500,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: isActive ? 'var(--rose)' : 'var(--text-secondary)',
        transition: 'color 0.3s ease',
      }}>
        {buttonLabel}
      </div>

      {/* Mute button when connected */}
      {isActive && (
        <button
          onClick={onMute}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            borderRadius: 'var(--radius)',
            border: `1px solid ${isMuted ? 'var(--rose)' : 'var(--border)'}`,
            background: isMuted ? 'rgba(244, 63, 94, 0.1)' : 'transparent',
            color: isMuted ? 'var(--rose)' : 'var(--text-secondary)',
            fontSize: '12px',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'var(--transition)',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            {isMuted ? (
              <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z"/>
            ) : (
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.4 4.58-5 4.92V19h2v2h-4v-2h2v-2.08C9.4 16.58 7 14.76 7 12H5c0 3.53 2.61 6.43 6 6.92V19h-1v-2h2v2h-1v.92c3.39-.49 6-3.39 6-6.92h-2z"/>
            )}
          </svg>
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
      )}

      {/* Audio level indicator */}
      {isActive && (
        <div style={{
          display: 'flex',
          gap: '3px',
          alignItems: 'flex-end',
          height: '24px',
        }}>
          {Array.from({ length: 7 }).map((_, i) => (
            <div
              key={i}
              style={{
                width: 3,
                height: `${Math.max(4, (isUserSpeaking ? audioLevel * 24 : 4) * (0.4 + Math.sin(i * 0.8) * 0.6))}px`,
                borderRadius: 2,
                background: isUserSpeaking ? 'var(--teal)' : 'var(--text-muted)',
                transition: 'height 0.1s ease, background 0.3s ease',
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
