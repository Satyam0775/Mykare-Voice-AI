import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Avatar from '../components/Avatar.jsx';
import VoiceOrb from '../components/VoiceOrb.jsx';
import ChatWindow from '../components/ChatWindow.jsx';
import ToolStatus from '../components/ToolStatus.jsx';
import CallSummary from '../components/CallSummary.jsx';
import { useVoice, CALL_STATE } from '../hooks/useVoice.js';
import { createChatWebSocket } from '../services/api.js';

export default function Home() {
  const {
    callState,
    isMuted,
    isAgentSpeaking,
    isUserSpeaking,
    transcript,
    toolActivity,
    error,
    roomName,
    audioLevel,
    sessionId,
    connectToRoom,
    disconnectFromRoom,
    toggleMute,
    addTranscript,
    addToolActivity,
  } = useVoice();

  const [showSummary, setShowSummary] = useState(false);
  const [activeTab, setActiveTab] = useState('transcript');
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsMessages, setWsMessages] = useState([]);
  const [wsInput, setWsInput] = useState('');
  const [wsToolActivity, setWsToolActivity] = useState([]);
  const [mode, setMode] = useState('voice'); // 'voice' | 'text'
  const [callDuration, setCallDuration] = useState(0);
  const durationRef = useRef(null);

  // Call duration timer
  useEffect(() => {
    if (callState === CALL_STATE.CONNECTED) {
      setCallDuration(0);
      durationRef.current = setInterval(() => setCallDuration(d => d + 1), 1000);
    } else {
      clearInterval(durationRef.current);
    }
    return () => clearInterval(durationRef.current);
  }, [callState]);

  const formatDuration = (s) => {
    const m = Math.floor(s / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  };

  // WebSocket text chat
  const connectWs = () => {
    if (wsRef.current) return;
    const ws = createChatWebSocket(uuidv4());
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'message') {
          setWsMessages(prev => [...prev, { id: uuidv4(), role: msg.role, content: msg.content, timestamp: new Date().toISOString() }]);
        } else if (msg.type === 'tool_call') {
          setWsToolActivity(prev => [{ id: uuidv4(), toolName: msg.tool_name, status: 'running', details: msg.tool_args, timestamp: new Date().toISOString() }, ...prev].slice(0, 20));
        } else if (msg.type === 'tool_result') {
          setWsToolActivity(prev => [{ id: uuidv4(), toolName: msg.tool_name, status: 'completed', details: msg.result, timestamp: new Date().toISOString() }, ...prev].slice(0, 20));
        }
      } catch (e) {}
    };

    ws.onclose = () => {
      setWsConnected(false);
      wsRef.current = null;
    };
  };

  const disconnectWs = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setWsConnected(false);
  };

  const sendWsMessage = () => {
    if (!wsInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const content = wsInput.trim();
    setWsMessages(prev => [...prev, { id: uuidv4(), role: 'user', content, timestamp: new Date().toISOString() }]);
    wsRef.current.send(JSON.stringify({ content }));
    setWsInput('');
  };

  const handleEndCall = async () => {
    await disconnectFromRoom();
    if (transcript.length > 0) {
      setShowSummary(true);
    }
  };

  const currentTranscript = mode === 'voice' ? transcript : wsMessages;
  const currentToolActivity = mode === 'voice' ? toolActivity : wsToolActivity;
  const isConnected = mode === 'voice'
    ? callState === CALL_STATE.CONNECTED
    : wsConnected;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-deep)',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background decoration */}
      <div style={{
        position: 'fixed',
        top: '-20%',
        right: '-10%',
        width: '600px',
        height: '600px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(14,165,233,0.06) 0%, transparent 70%)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />
      <div style={{
        position: 'fixed',
        bottom: '-20%',
        left: '-10%',
        width: '500px',
        height: '500px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(45,212,191,0.04) 0%, transparent 70%)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />

      {/* Header */}
      <header style={{
        position: 'relative',
        zIndex: 10,
        padding: '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(6,13,26,0.8)',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #0ea5e9, #2dd4bf)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
              <path d="M12 1a11 11 0 100 22A11 11 0 0012 1zM9 8.5A1.5 1.5 0 1110.5 7 1.5 1.5 0 019 8.5zm6 0A1.5 1.5 0 1116.5 7 1.5 1.5 0 0115 8.5zm1.92 5.34A6 6 0 016.08 13.8a.75.75 0 01.64-1.35A4.5 4.5 0 0012 14a4.5 4.5 0 005.28-1.55.75.75 0 011.14.97z"/>
            </svg>
          </div>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontSize: '18px',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
            }}>
              Mykare
              <span className="gradient-text"> Voice AI</span>
            </div>
            <div style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-body)',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}>
              Healthcare Assistant
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Mode toggle */}
          <div style={{
            display: 'flex',
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border)',
            padding: '3px',
            gap: '2px',
          }}>
            {['voice', 'text'].map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                style={{
                  padding: '5px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  background: mode === m ? 'linear-gradient(135deg, rgba(14,165,233,0.2), rgba(14,165,233,0.1))' : 'transparent',
                  color: mode === m ? 'var(--cyan)' : 'var(--text-muted)',
                  fontFamily: 'var(--font-display)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  letterSpacing: '0.04em',
                  transition: 'var(--transition)',
                  textTransform: 'capitalize',
                }}
              >
                {m === 'voice' ? '🎙 Voice' : '💬 Text'}
              </button>
            ))}
          </div>

          {/* Status indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: 'var(--radius)',
            background: 'var(--bg-card)',
            border: `1px solid ${isConnected ? 'rgba(16,185,129,0.3)' : 'var(--border)'}`,
          }}>
            <div style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: isConnected ? 'var(--emerald)' : 'var(--text-muted)',
              boxShadow: isConnected ? '0 0 6px var(--emerald)' : 'none',
              animation: isConnected ? 'pulse-ring 2s infinite' : 'none',
            }} />
            <span style={{
              fontSize: '11px',
              fontFamily: 'var(--font-body)',
              color: isConnected ? 'var(--emerald)' : 'var(--text-muted)',
              fontWeight: 500,
            }}>
              {callState === CALL_STATE.CONNECTING ? 'Connecting…'
                : isConnected ? callState === CALL_STATE.CONNECTED ? `Live · ${formatDuration(callDuration)}` : 'Connected'
                : 'Offline'}
            </span>
          </div>

          {/* Summary button */}
          {currentTranscript.length > 0 && (
            <button
              onClick={() => setShowSummary(true)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border-bright)',
                background: 'transparent',
                color: 'var(--cyan)',
                fontFamily: 'var(--font-display)',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                letterSpacing: '0.04em',
                transition: 'var(--transition)',
              }}
            >
              📝 Summary
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main style={{
        flex: 1,
        display: 'flex',
        position: 'relative',
        zIndex: 1,
        overflow: 'hidden',
      }}>
        {/* Left panel - Avatar & controls */}
        <div style={{
          width: '320px',
          flexShrink: 0,
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '40px 32px',
          gap: '32px',
          background: 'rgba(6,13,26,0.4)',
        }}>
          {/* Avatar */}
          <Avatar
            isAgentSpeaking={isAgentSpeaking}
            isUserSpeaking={isUserSpeaking}
            callState={callState}
          />

          {/* Room info */}
          {roomName && (
            <div style={{
              padding: '8px 14px',
              borderRadius: 'var(--radius)',
              background: 'rgba(14,165,233,0.06)',
              border: '1px solid var(--border)',
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-body)',
              textAlign: 'center',
              letterSpacing: '0.04em',
            }}>
              Room: {roomName}
            </div>
          )}

          {/* Voice controls */}
          {mode === 'voice' && (
            <VoiceOrb
              callState={callState}
              isAgentSpeaking={isAgentSpeaking}
              isUserSpeaking={isUserSpeaking}
              audioLevel={audioLevel}
              onConnect={connectToRoom}
              onDisconnect={handleEndCall}
              onMute={toggleMute}
              isMuted={isMuted}
            />
          )}

          {/* Text chat controls */}
          {mode === 'text' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              {!wsConnected ? (
                <button
                  onClick={connectWs}
                  style={{
                    padding: '12px 28px',
                    borderRadius: 'var(--radius)',
                    border: 'none',
                    background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                    color: 'white',
                    fontFamily: 'var(--font-display)',
                    fontWeight: 700,
                    fontSize: '14px',
                    cursor: 'pointer',
                    boxShadow: '0 0 24px rgba(14,165,233,0.3)',
                    letterSpacing: '0.04em',
                    transition: 'var(--transition)',
                  }}
                >
                  💬 Start Chat
                </button>
              ) : (
                <button
                  onClick={disconnectWs}
                  style={{
                    padding: '12px 28px',
                    borderRadius: 'var(--radius)',
                    border: 'none',
                    background: 'linear-gradient(135deg, #f43f5e, #e11d48)',
                    color: 'white',
                    fontFamily: 'var(--font-display)',
                    fontWeight: 700,
                    fontSize: '14px',
                    cursor: 'pointer',
                    letterSpacing: '0.04em',
                  }}
                >
                  End Chat
                </button>
              )}
              {wsConnected && wsMessages.length > 0 && (
                <button
                  onClick={() => setShowSummary(true)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--radius)',
                    border: '1px solid var(--border-bright)',
                    background: 'transparent',
                    color: 'var(--cyan)',
                    fontFamily: 'var(--font-display)',
                    fontWeight: 600,
                    fontSize: '12px',
                    cursor: 'pointer',
                    letterSpacing: '0.04em',
                  }}
                >
                  📝 Generate Summary
                </button>
              )}
            </div>
          )}

          {/* Error display */}
          {error && (
            <div style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius)',
              background: 'rgba(244,63,94,0.08)',
              border: '1px solid rgba(244,63,94,0.2)',
              fontSize: '12px',
              color: 'var(--rose)',
              fontFamily: 'var(--font-body)',
              textAlign: 'center',
              lineHeight: 1.4,
            }}>
              {error}
            </div>
          )}

          {/* Info cards */}
          <div style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            marginTop: 'auto',
          }}>
            {[
              { icon: '📅', label: 'Book Appointments' },
              { icon: '🔄', label: 'Reschedule & Cancel' },
              { icon: '📋', label: 'View Your History' },
            ].map(item => (
              <div key={item.label} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-hover)',
                border: '1px solid var(--border)',
                fontSize: '12px',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-body)',
              }}>
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel - Transcript & Tool Activity */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {/* Tabs */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--border)',
            background: 'rgba(6,13,26,0.6)',
            padding: '0 24px',
          }}>
            {[
              { id: 'transcript', label: 'Live Transcript', count: currentTranscript.filter(m => m.role !== 'system').length },
              { id: 'tools', label: 'Tool Activity', count: currentToolActivity.length },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '16px 0',
                  marginRight: '28px',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-display)',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: activeTab === tab.id ? 'var(--cyan)' : 'var(--text-muted)',
                  borderBottom: activeTab === tab.id ? '2px solid var(--cyan)' : '2px solid transparent',
                  transition: 'var(--transition)',
                  letterSpacing: '0.04em',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 18,
                    height: 18,
                    borderRadius: '50%',
                    background: activeTab === tab.id ? 'var(--cyan)' : 'var(--bg-card)',
                    color: activeTab === tab.id ? 'var(--bg-deep)' : 'var(--text-muted)',
                    fontSize: '10px',
                    fontWeight: 700,
                  }}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Panel content */}
          <div style={{
            flex: 1,
            padding: '20px 24px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}>
            {activeTab === 'transcript' ? (
              <>
                <ChatWindow transcript={currentTranscript} />

                {/* Text input for text mode */}
                {mode === 'text' && wsConnected && (
                  <div style={{
                    marginTop: '16px',
                    display: 'flex',
                    gap: '8px',
                  }}>
                    <input
                      value={wsInput}
                      onChange={e => setWsInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendWsMessage()}
                      placeholder="Type your message…"
                      style={{
                        flex: 1,
                        padding: '12px 16px',
                        borderRadius: 'var(--radius)',
                        border: '1px solid var(--border)',
                        background: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-body)',
                        fontSize: '14px',
                        outline: 'none',
                        transition: 'var(--transition)',
                      }}
                    />
                    <button
                      onClick={sendWsMessage}
                      disabled={!wsInput.trim()}
                      style={{
                        padding: '12px 20px',
                        borderRadius: 'var(--radius)',
                        border: 'none',
                        background: wsInput.trim()
                          ? 'linear-gradient(135deg, #0ea5e9, #0284c7)'
                          : 'var(--bg-card)',
                        color: wsInput.trim() ? 'white' : 'var(--text-muted)',
                        fontFamily: 'var(--font-display)',
                        fontWeight: 600,
                        fontSize: '13px',
                        cursor: wsInput.trim() ? 'pointer' : 'not-allowed',
                        transition: 'var(--transition)',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Send
                    </button>
                  </div>
                )}
              </>
            ) : (
              <ToolStatus activities={currentToolActivity} />
            )}
          </div>
        </div>
      </main>

      {/* Call Summary Modal */}
      <CallSummary
        transcript={currentTranscript}
        onClose={() => setShowSummary(false)}
        isVisible={showSummary}
      />
    </div>
  );
}
