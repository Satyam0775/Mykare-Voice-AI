import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Room,
  RoomEvent,
  Track,
  TrackEvent,
  LocalParticipant,
  RemoteParticipant,
  DataPacket_Kind,
} from 'livekit-client';
import { v4 as uuidv4 } from 'uuid';
import { getVoiceToken } from '../services/api.js';

export const CALL_STATE = {
  IDLE: 'idle',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTING: 'disconnecting',
  ERROR: 'error',
};

export function useVoice() {
  const [callState, setCallState] = useState(CALL_STATE.IDLE);
  const [isMuted, setIsMuted] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [toolActivity, setToolActivity] = useState([]);
  const [error, setError] = useState(null);
  const [roomName, setRoomName] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const roomRef = useRef(null);
  const sessionIdRef = useRef(uuidv4());
  const audioLevelIntervalRef = useRef(null);

  const addTranscript = useCallback((role, content) => {
    setTranscript(prev => [
      ...prev,
      { id: uuidv4(), role, content, timestamp: new Date().toISOString() },
    ]);
  }, []);

  const addToolActivity = useCallback((toolName, status, details) => {
    const activity = {
      id: uuidv4(),
      toolName,
      status,
      details,
      timestamp: new Date().toISOString(),
    };
    setToolActivity(prev => [activity, ...prev].slice(0, 20));
  }, []);

  const connectToRoom = useCallback(async () => {
    if (callState !== CALL_STATE.IDLE) return;

    setCallState(CALL_STATE.CONNECTING);
    setError(null);
    setTranscript([]);
    setToolActivity([]);

    try {
      const participantName = `patient-${uuidv4().slice(0, 6)}`;
      const tokenData = await getVoiceToken(participantName, null);
      const { token, room_name: rn, livekit_url } = tokenData;

      setRoomName(rn);

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      roomRef.current = room;

      // Room events
      room.on(RoomEvent.Connected, () => {
        setCallState(CALL_STATE.CONNECTED);
        addTranscript('system', 'Connected to Mykare Healthcare AI');
      });

      room.on(RoomEvent.Disconnected, () => {
        setCallState(CALL_STATE.IDLE);
        clearInterval(audioLevelIntervalRef.current);
      });

      room.on(RoomEvent.TrackSubscribed, (track, pub, participant) => {
        if (track.kind === Track.Kind.Audio) {
          const audioEl = track.attach();
          audioEl.play().catch(console.error);

          track.on(TrackEvent.AudioPlaybackStarted, () => {
            setIsAgentSpeaking(true);
          });
          track.on(TrackEvent.AudioPlaybackFailed, () => {
            setIsAgentSpeaking(false);
          });
        }
      });

      room.on(RoomEvent.TrackUnsubscribed, () => {
        setIsAgentSpeaking(false);
      });

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        const hasAgent = speakers.some(s => s instanceof RemoteParticipant);
        const hasLocal = speakers.some(s => s instanceof LocalParticipant);
        setIsAgentSpeaking(hasAgent);
        setIsUserSpeaking(hasLocal);
      });

      // Data messages from agent
      room.on(RoomEvent.DataReceived, (data, participant) => {
        try {
          const decoded = new TextDecoder().decode(data);
          const msg = JSON.parse(decoded);

          if (msg.type === 'transcript') {
            addTranscript(msg.role || 'assistant', msg.content);
          } else if (msg.type === 'tool_call') {
            addToolActivity(msg.tool_name, 'running', msg.args);
          } else if (msg.type === 'tool_result') {
            addToolActivity(msg.tool_name, 'completed', msg.result);
          }
        } catch (e) {
          // non-JSON data
        }
      });

      room.on(RoomEvent.ConnectionQualityChanged, (quality, participant) => {
        if (participant instanceof LocalParticipant && quality === 'poor') {
          setError('Connection quality is poor. Audio may be affected.');
        }
      });

      await room.connect(livekit_url, token);
      await room.localParticipant.enableMicrophone();

      // Poll audio level
      audioLevelIntervalRef.current = setInterval(() => {
        const pub = room.localParticipant.audioTrackPublications.values().next().value;
        if (pub?.track) {
          const level = pub.track.currentBitrate || 0;
          setAudioLevel(Math.min(level / 50000, 1));
        }
      }, 100);

    } catch (err) {
      console.error('Voice connection error:', err);
      setError(err.message || 'Failed to connect');
      setCallState(CALL_STATE.ERROR);
    }
  }, [callState, addTranscript, addToolActivity]);

  const disconnectFromRoom = useCallback(async () => {
    setCallState(CALL_STATE.DISCONNECTING);
    clearInterval(audioLevelIntervalRef.current);
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    setCallState(CALL_STATE.IDLE);
    setIsAgentSpeaking(false);
    setIsUserSpeaking(false);
    setAudioLevel(0);
  }, []);

  const toggleMute = useCallback(async () => {
    if (!roomRef.current) return;
    const muted = !isMuted;
    await roomRef.current.localParticipant.setMicrophoneEnabled(!muted);
    setIsMuted(muted);
  }, [isMuted]);

  useEffect(() => {
    return () => {
      clearInterval(audioLevelIntervalRef.current);
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  return {
    callState,
    isMuted,
    isAgentSpeaking,
    isUserSpeaking,
    transcript,
    toolActivity,
    error,
    roomName,
    audioLevel,
    sessionId: sessionIdRef.current,
    connectToRoom,
    disconnectFromRoom,
    toggleMute,
    addTranscript,
    addToolActivity,
  };
}
