# Mykare Voice AI — Healthcare Front-Desk Agent

A production-ready, end-to-end voice AI system for healthcare front-desk operations.

```
User Speech → Deepgram STT → OpenRouter (Meta Llama 3.3 70B) → Healthcare Tools → Cartesia TTS → LiveKit Agent → React Frontend
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Voice transport | LiveKit Agents 1.6.3 (Agent + AgentSession architecture) |
| STT | Deepgram Nova-2 |
| TTS | Cartesia Sonic-2 |
| LLM primary | OpenRouter — meta-llama/llama-3.3-70b-instruct:free |
| LLM fallback | Grok (grok-beta via api.x.ai) |
| Avatar | Beyond Presence (optional animated fallback) |
| Backend | FastAPI + Python 3.11.9 |
| Database | SQLite + SQLAlchemy (async) |
| Frontend | React 19 + Vite 7 |

---

## Project Structure

```
mykare-voice-ai/
├── backend/
│   ├── app/
│   │   ├── agent/          voice_agent.py  — LiveKit Agent + AgentSession
│   │   ├── api/            routes.py, websocket.py
│   │   ├── db/             database.py, models.py
│   │   ├── schemas/        schemas.py
│   │   ├── services/       llm_service.py, stt_service.py, tts_service.py
│   │   ├── tools/          appointment_tools.py  (8 tools)
│   │   ├── utils/          logger.py, token.py
│   │   └── config.py
│   ├── main.py             FastAPI entry point
│   ├── agent_worker.py     LiveKit worker entry point
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/     Avatar, VoiceControls, TranscriptPanel,
    │   │                   ToolActivityPanel, AppointmentPanel, SummaryPanel
    │   ├── hooks/          useLiveKit.js, useVoiceAgent.js
    │   ├── pages/          Dashboard.jsx
    │   ├── services/       api.js
    │   └── styles/         index.css
    ├── package.json
    └── .env.example
```

---

## Prerequisites

- Python 3.11.9
- Node.js 20+
- A running LiveKit server (local or cloud)
- API keys: OpenRouter, Deepgram, Cartesia, (optional) Grok, (optional) Beyond Presence

### Quick LiveKit server (Docker)

```bash
docker run --rm \
  -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: devsecret" \
  livekit/livekit-server --dev
```

---

## Setup

### 1. Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in your API keys
```

### 2. Frontend

```bash
cd frontend

npm install

cp .env.example .env
# Edit .env — set VITE_LIVEKIT_URL if not using localhost
```

---

## Running Locally

Open **4 terminal windows**.

### Terminal 1 — LiveKit server

```bash
docker run --rm \
  -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: devsecret" \
  livekit/livekit-server --dev
```

### Terminal 2 — FastAPI backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 3 — LiveKit agent worker

```bash
cd backend
source venv/bin/activate
python agent_worker.py dev
```

### Terminal 4 — React frontend

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Keys Reference

| Variable | Where to get |
|----------|-------------|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `DEEPGRAM_API_KEY` | https://console.deepgram.com |
| `CARTESIA_API_KEY` | https://play.cartesia.ai |
| `LIVEKIT_URL` | Your LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit dashboard / config |
| `LIVEKIT_API_SECRET` | LiveKit dashboard / config |
| `VITE_BP_AGENT_ID` | https://app.beyondpresence.ai (optional) |

---

## Conversation Flow

1. User clicks **Start Call** → frontend requests LiveKit token from FastAPI
2. FastAPI dispatches the agent worker to the room via LiveKit API
3. Agent connects using LiveKit Agents v1.6.3 `Agent + AgentSession` architecture: Deepgram STT listens, OpenRouter LLM processes, Cartesia TTS responds
4. Agent broadcasts events over LiveKit data channels:
   - `transcript` — real-time STT/LLM turn text
   - `tool-events` — real-time tool status updates
   - `appointments` — appointment list after mutations
   - `summary` — end-of-call summary JSON
   - `state` — speaking/listening state for avatar sync
5. User clicks **End Call** → `end_conversation` tool generates summary

---

## Tools

The agent uses **8 tools** for healthcare front-desk operations:

| Tool | Description |
|------|-------------|
| `identify_user` | Collect phone number, look up patient record |
| `register_patient` | Create a new patient record (called after identify_user returns found=false) |
| `fetch_slots` | Return hardcoded available appointment slots |
| `book_appointment` | Save to SQLite, prevent double-booking |
| `retrieve_appointments` | List user's existing appointments |
| `modify_appointment` | Reschedule an appointment |
| `cancel_appointment` | Cancel an appointment |
| `end_conversation` | Generate & broadcast call summary |

---

## Beyond Presence Avatar

Set `VITE_BP_AGENT_ID` in `frontend/.env` to your Beyond Presence agent ID.  
If blank, the app uses the built-in animated SVG avatar.

---

## Cost Per Call (Estimate)

| Service | Rate | Per 5-min call |
|---------|------|---------------|
| Deepgram Nova-2 | $0.0043/min | ~$0.022 |
| Cartesia Sonic-2 | ~$0.005/min TTS audio | ~$0.025 |
| OpenRouter llama-3.3-70b:free | Free | $0.00 |
| LiveKit | $0.00/min (self-hosted) | $0.00 |
| **Total** | | **~$0.05** |

---

## Troubleshooting

**Agent doesn't join the room**  
Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` match in both `.env` and the LiveKit server config.

**No audio / STT not working**  
Browser must have microphone permission. Check HTTPS if deployed (LiveKit requires HTTPS in production).

**OpenRouter 429 / quota exceeded**  
The agent automatically falls back to Grok. Set `GROQ_API_KEY` to ensure fallback works.

**SQLite locked errors**  
Only one agent worker should connect to the same `.db` file at a time. Use unique DB paths per deployment if running multiple workers.

**livekit-agents chat_context.py IndentationError or AttributeError**  
Run the included patch script once before starting the worker:
```bash
python fix_livekit_bug.py
```
This fixes a known bug in livekit-agents 1.5.x and 1.6.x where the chat context serializer crashes on plain string system prompts.
