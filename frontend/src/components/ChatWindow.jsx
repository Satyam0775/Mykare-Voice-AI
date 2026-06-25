import React, { useEffect, useRef } from 'react';

function TranscriptBubble({ msg }) {
  const isUser = msg.role === 'user';
  const isSystem = msg.role === 'system';
  const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isSystem) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '6px 12px',
        animation: 'fade-up 0.3s ease both',
      }}>
        <span style={{
          fontSize: '11px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-body)',
          letterSpacing: '0.04em',
        }}>
          {msg.content}
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        animation: 'fade-up 0.3s ease both',
        gap: '3px',
      }}
    >
      <div style={{
        maxWidth: '85%',
        padding: '10px 14px',
        borderRadius: isUser
          ? 'var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg)'
          : 'var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg)',
        background: isUser
          ? 'linear-gradient(135deg, rgba(14,165,233,0.2), rgba(14,165,233,0.1))'
          : 'rgba(255,255,255,0.04)',
        border: isUser
          ? '1px solid rgba(14,165,233,0.3)'
          : '1px solid var(--border)',
        fontSize: '13px',
        lineHeight: 1.5,
        color: 'var(--text-primary)',
        fontFamily: 'var(--font-body)',
        wordBreak: 'break-word',
      }}>
        {msg.content}
      </div>
      <div style={{
        fontSize: '10px',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-body)',
        paddingLeft: isUser ? 0 : '4px',
        paddingRight: isUser ? '4px' : 0,
      }}>
        {isUser ? 'You' : 'Mykare AI'} · {time}
      </div>
    </div>
  );
}

export default function ChatWindow({ transcript }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  if (!transcript || transcript.length === 0) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        color: 'var(--text-muted)',
      }}>
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
        <div style={{ fontSize: '13px', fontFamily: 'var(--font-body)', textAlign: 'center' }}>
          <div style={{ marginBottom: '4px', fontWeight: 500, color: 'var(--text-secondary)' }}>Live Transcript</div>
          <div>Start a call to see the conversation here</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      padding: '4px 0',
    }}>
      {transcript.map(msg => (
        <TranscriptBubble key={msg.id} msg={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
