import { useState, useEffect, useRef, useCallback } from "react";
import {
  Room,
  RoomEvent,
  Track,
  TrackEvent,
  DataPacket_Kind,
  ConnectionState,
} from "livekit-client";

const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL || "ws://localhost:7880";

export function useLiveKit({ onTranscript, onToolEvent, onAppointmentUpdate, onSummary, onStateChange }) {
  const roomRef = useRef(null);
  const [connectionState, setConnectionState] = useState("disconnected");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [localMuted, setLocalMuted] = useState(false);

  const handleDataReceived = useCallback(
    (payload, participant, _kind, topic) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);

        if (topic === "transcript") {
          onTranscript?.(data);
        } else if (topic === "tool-events") {
          onToolEvent?.(data);
        } else if (topic === "appointments") {
          onAppointmentUpdate?.(data);
        } else if (topic === "summary") {
          onSummary?.(data);
        } else if (topic === "state") {
          if (data.speaking !== undefined) setIsSpeaking(data.speaking);
          if (data.listening !== undefined) setIsListening(data.listening);
          onStateChange?.(data);
        }
      } catch (err) {
        console.error("[LiveKit] dataReceived parse error", err);
      }
    },
    [onTranscript, onToolEvent, onAppointmentUpdate, onSummary, onStateChange]
  );

  const connect = useCallback(async (token) => {
    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
      audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });

    room.on(RoomEvent.Connected, () => {
      setConnectionState("connected");
      console.info("[LiveKit] connected", room.name);
    });
    room.on(RoomEvent.Disconnected, () => {
      setConnectionState("disconnected");
      setIsSpeaking(false);
      setIsListening(false);
    });
    room.on(RoomEvent.Reconnecting, () => setConnectionState("reconnecting"));
    room.on(RoomEvent.Reconnected, () => setConnectionState("connected"));
    room.on(RoomEvent.DataReceived, handleDataReceived);

    // Auto-play remote audio tracks (agent TTS output)
    room.on(RoomEvent.TrackSubscribed, (track, _pub, participant) => {
      if (track.kind === Track.Kind.Audio) {
        const audioEl = track.attach();
        audioEl.autoplay = true;
        document.body.appendChild(audioEl);
        track.on(TrackEvent.Ended, () => audioEl.remove());
      }
    });

    // Detect agent speaking via active speaker events
    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const agentSpeaking = speakers.some((s) => s.identity !== room.localParticipant?.identity);
      setIsSpeaking(agentSpeaking);
    });

    setConnectionState("connecting");
    console.log("LiveKit URL:", LIVEKIT_URL);
    await room.connect(LIVEKIT_URL, token, { autoSubscribe: true });

    // Enable local microphone
    await room.localParticipant.setMicrophoneEnabled(true);
    setIsListening(true);

    roomRef.current = room;
    return room;
  }, [handleDataReceived]);

  const disconnect = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    setConnectionState("disconnected");
    setIsSpeaking(false);
    setIsListening(false);
  }, []);

  const toggleMute = useCallback(async () => {
    if (!roomRef.current) return;
    const enabled = !localMuted;
    await roomRef.current.localParticipant.setMicrophoneEnabled(!enabled);
    setLocalMuted(enabled);
  }, [localMuted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
    };
  }, []);

  return {
    connect,
    disconnect,
    toggleMute,
    connectionState,
    isSpeaking,
    isListening,
    localMuted,
    room: roomRef.current,
  };
}
