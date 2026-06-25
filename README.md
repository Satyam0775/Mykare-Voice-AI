# Mykare Voice AI — Healthcare Front-Desk Agent

> A production-ready, end-to-end voice AI system for healthcare front-desk operations — powered by LiveKit, Deepgram, OpenRouter (Llama 3.3 70B), and Cartesia.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MYKARE VOICE AI PIPELINE                       │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌───────────────┐     ┌──────────────────────────┐
  │  User    │────▶│  Deepgram     │────▶│  OpenRouter              │
  │  Speech  │     │  Nova-2 (STT) │     │  Llama 3.3 70B (LLM)    │
  └──────────┘     └───────────────┘     │  ── fallback: Grok Beta ─│
                                         └────────────┬─────────────┘
                                                      │
                                         ┌────────────▼─────────────┐
                                         │   Healthcare Tools (×8)  │
                                         │  identify_user           │
                                         │  register_patient        │
                                         │  fetch_slots             │
                                         │  book_appointment        │
                                         │  retrieve_appointments   │
                                         │  modify_appointment      │
                                         │  cancel_appointment      │
                                         │  end_conversation        │
                                         └────────────┬─────────────┘
                                                      │
  ┌──────────┐     ┌───────────────┐     ┌────────────▼─────────────┐
  │  React   │◀────│  LiveKit      │◀────│  Cartesia                │
  │  Frontend│     │  Agent        │     │  Sonic-2 (TTS)           │
  │  (UI)    │     │  (Transport)  │     └──────────────────────────┘
  └──────────┘     └───────────────┘
        │
        │   LiveKit Data Channels
        ├── transcript   → real-time STT / LLM turn text
        ├── tool-events  → live tool status updates
        ├── appointments → appointment list after mutations
        ├── summary      → end-of-call summary JSON
        └── state        → speaking / listening (avatar sync)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Voice transport | LiveKit Agents 1.6.3 (Agent + AgentSession) |
| Speech-to-text | Deepgram Nova-2 |
| Text-to-speech | Cartesia Sonic-2 |
| LLM (primary) | OpenRouter — `meta-llama/llama-3.3-70b-instruct:free` |
| LLM (fallback) | Grok Beta via `api.x.ai` |
| Avatar (optional) | Beyond Presence animated agent |
| Backend | FastAPI + Python 3.11.9 |
| Database | SQLite + SQLAlchemy (async) |
| Frontend | React 19 + Vite 7 |

---

## Project Structure

```
mykare-voice-ai/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   └── voice_agent.py        # LiveKit Agent + AgentSession
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── websocket.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── stt_service.py
│   │   │   └── tts_service.py
│   │   ├── tools/
│   │   │   └── appointment_tools.py  # 8 healthcare tools
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   └── token.py
│   │   └── config.py
│   ├── main.py                       # FastAPI entry point
│   ├── agent_worker.py               # LiveKit worker entry point
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Avatar
    │   │   ├── VoiceControls
    │   │   ├── TranscriptPanel
    │   │   ├── ToolActivityPanel
    │   │   ├── AppointmentPanel
    │   │   └── SummaryPanel
    │   ├── hooks/
    │   │   ├── useLiveKit.js
    │   │   └── useVoiceAgent.js
    │   ├── pages/
    │   │   └── Dashboard.jsx
    │   ├── services/
    │   │   └── api.js
    │   └── styles/
    │       └── index.css
    ├── package.json
    └── .env.example
```

---

## Prerequisites

- Python 3.11.9
- Node.js 20+
- A running LiveKit server (local or cloud)
- API keys for: OpenRouter, Deepgram, Cartesia, and optionally Grok and Beyond Presence

### Start a local LiveKit server (Docker)

```bash
docker run --rm \
  -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: devsecret" \
  livekit/livekit-server --dev
```

---

## Setup

### Backend

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys
```

### Frontend

```bash
cd frontend

npm install

cp .env.example .env
# Edit .env — set VITE_LIVEKIT_URL if not using localhost
```

---

## Running Locally

Open **4 terminal windows** and run each process in its own window.

**Terminal 1 — LiveKit server**
```bash
docker run --rm \
  -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: devsecret" \
  livekit/livekit-server --dev
```

**Terminal 2 — FastAPI backend**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — LiveKit agent worker**
```bash
cd backend
source venv/bin/activate
python agent_worker.py dev
```

**Terminal 4 — React frontend**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## API Keys Reference

| Environment Variable | Where to Get It |
|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `DEEPGRAM_API_KEY` | https://console.deepgram.com |
| `CARTESIA_API_KEY` | https://play.cartesia.ai |
| `LIVEKIT_URL` | Your LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit dashboard / server config |
| `LIVEKIT_API_SECRET` | LiveKit dashboard / server config |
| `VITE_BP_AGENT_ID` | https://app.beyondpresence.ai *(optional)* |

---

## Conversation Flow

```
1. User clicks "Start Call"
        │
        ▼
2. Frontend requests a LiveKit token from FastAPI
        │
        ▼
3. FastAPI dispatches the agent worker into the room via LiveKit API
        │
        ▼
4. Agent connects (LiveKit Agents v1.6.3):
   Deepgram STT listens → OpenRouter LLM processes → Cartesia TTS responds
        │
        ▼
5. Agent broadcasts real-time events over LiveKit data channels:
   ├── transcript   — live STT / LLM turn text
   ├── tool-events  — tool call status updates
   ├── appointments — updated appointment list after any mutation
   ├── summary      — end-of-call JSON summary
   └── state        — speaking / listening state for avatar sync
        │
        ▼
6. User clicks "End Call" → end_conversation tool generates & broadcasts summary
```

---

## Healthcare Tools

The agent is equipped with **8 purpose-built tools** for front-desk operations:

| Tool | Description |
|---|---|
| `identify_user` | Collect phone number and look up existing patient record |
| `register_patient` | Create a new patient record (called when `identify_user` returns `found=false`) |
| `fetch_slots` | Return available appointment slots |
| `book_appointment` | Save appointment to SQLite; prevents double-booking |
| `retrieve_appointments` | List all existing appointments for the patient |
| `modify_appointment` | Reschedule an existing appointment |
| `cancel_appointment` | Cancel an existing appointment |
| `end_conversation` | Generate and broadcast end-of-call summary |

---

## Avatar

Set `VITE_BP_AGENT_ID` in `frontend/.env` to your Beyond Presence agent ID to enable a live animated avatar. If left blank, the app automatically falls back to the built-in animated SVG avatar.

---

## Cost Estimate (Per 5-Minute Call)

| Service | Rate | Estimated Cost |
|---|---|---|
| Deepgram Nova-2 | $0.0043 / min | ~$0.022 |
| Cartesia Sonic-2 | ~$0.005 / min | ~$0.025 |
| OpenRouter Llama 3.3 70B (free tier) | $0.00 | $0.00 |
| LiveKit (self-hosted) | $0.00 / min | $0.00 |
| **Total** | | **~$0.05** |

---

## Troubleshooting

**Agent doesn't join the room**
Verify that `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` match exactly in both your `.env` file and the LiveKit server configuration.

**No audio / STT not working**
The browser must have microphone permission granted. If deploying to production, LiveKit requires HTTPS — ensure your deployment uses a valid TLS certificate.

**OpenRouter 429 / quota exceeded**
The agent automatically falls back to Grok. Set `GROQ_API_KEY` in your `.env` to ensure the fallback is available.

**SQLite locked errors**
Only one agent worker should connect to the same `.db` file at a time. If running multiple workers, configure each with a unique database file path.

**`livekit-agents` IndentationError or AttributeError in `chat_context.py`**
Run the included patch script once before starting the agent worker:
```bash
python fix_livekit_bug.py
```
This resolves a known bug in `livekit-agents` 1.5.x and 1.6.x where the chat context serializer crashes on plain string system prompts.

---

## License

MIT
