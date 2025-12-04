# Real-Time Speech-to-Text Transcriber (CPU-only • 100% Open-Source)

A privacy-first, browser-based **speech-to-text** application that works completely offline.

- Live transcription using the open-source **Vosk** model (CPU only)  
- Microphone → WebSocket → FastAPI → instant text in the browser  
- Every session saved with transcript, word count, and timestamps  
- Modern React frontend + fully Dockerized backend  
- Zero cloud, zero GPU, zero internet after setup  

Ideal for offline transcription, local AI demos, or learning real-time speech-to-text systems.

### System Architecture
![0](https://github.com/shovonSharma/speech-transcriber/blob/main/0.jpeg)

### Why This Stack?
```bash
| Layer          | Technology         | Why It’s Perfect Here                                                                 |
|----------------|--------------------|---------------------------------------------------------------------------------------|
| Speech Engine  | **Vosk**           | 100% offline • open-source • tiny (~40 MB) • real-time • excellent CPU-only accuracy  |
| Backend        | **FastAPI**        | Async-native (WebSockets) • blazing fast • auto-generated docs                        |
| Database       | **SQLite**         | Zero-config • lightweight • fully persistent • no server needed                       |
| Frontend       | **React + Vite**   | Instant hot-reload • modern components • ideal for live transcription updates         |
| Deployment     | **Docker Compose** | One command to run everything — no Python/Node install required on any machine        |
```

Result → A complete, privacy-first, real-time speech-to-text app that runs anywhere with zero cloud, zero GPU, and zero internet after first launch.
.

### project structure

```bash
speech-transcriber/
├── .dockerignore                  
├── docker-compose.yml             
├── README.md                      
│
├── backend/
│   ├── Dockerfile                 
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── requirements.txt
│   ├── test_api.py
│   ├── db.sqlite                  # ← will be created here automatically
│   └── model/
│       └── vosk-model-small-en-us-0.15/   # ← extract model here 
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js            
│   ├── index.html
│   └── src/
│       ├── main.jsx               
│       ├── App.jsx
│       └── components/
│           ├── StartStop.jsx
│           ├── LivePartial.jsx
│           ├── FinalTranscript.jsx
│           └── Stats.jsx
│
└── venv/                          # ← keep venv, ignored by Docker
```

###  Download & Place the Vosk Model

```bash
cd backend

# Create model folder
mkdir -p model

# Download small English model (~40MB, perfect for CPU)
wget -O vosk-model-small.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip

# Or use the one you already have (0.15 is also fine)
# Just make sure it's EXTRACTED into: backend/model/vosk-model-small-en-us-0.15/

unzip vosk-model-small.zip -d model/
# → results in: model/vosk-model-small-en-us-0.15/
```

### To run the model

#### Option 1: Local development 
```bash
# Terminal 1 – Frontend (React + Vite)
cd frontend
npm install
npm run dev
# → opens http://localhost:3000

# Terminal 2 – Backend (FastAPI + Vosk)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 2: Docker
```bash
# First time (downloads images, builds, starts)
docker-compose up --build

# Later (just start)
docker-compose up

# Or run in background
docker-compose up -d
```

### User Interface
![1](https://github.com/shovonSharma/speech-transcriber/blob/main/1.png)

### Database

#### Database Schema (`sessions` table)

```bash

| Column       | Type         | Constraints / Notes                            | Description                            |
|--------------|--------------|------------------------------------------------|----------------------------------------|
| `id`         | INTEGER      | `PRIMARY KEY`, `AUTOINCREMENT`                 | Unique session ID                      |
| `start_ts`   | DATETIME     | `NOT NULL`, default `CURRENT_TIMESTAMP` (UTC)  | When recording started (UTC)           |
| `end_ts`     | DATETIME     | `NULLABLE`                                     | When recording ended (UTC)             |
| `duration`   | INTEGER      | `NULLABLE` (seconds)                           | Audio duration in seconds              |
| `word_count` | INTEGER      | `NULLABLE`, default `0`                        | Number of words in final transcript    |
| `transcript` | TEXT         | `NULLABLE`                                     | Full final transcript (plain text)     |
```

#### Example row (JSON from `GET /sessions/{id}`)
```json
{
  "id": 42,
  "start": "2025-04-05T14:22:10.123456",
  "end": "2025-04-05T14:23:18.987654",
  "duration": 68,
  "word_count": 156,
  "transcript": "this is a real time speech to text application running entirely on cpu using the open source vosk model..."
}
```

![2](https://github.com/shovonSharma/speech-transcriber/blob/main/2.png)

### Testing
#### TEST-1 → Proves FastAPI starts + Vosk model loads successfully

#### TEST-2 → Proves core real-time flow works (WebSocket → receives audio → Vosk processes it → saves to DB → appears in /sessions)

#### TEST-3 → Proves REST API returns the full transcript + metadata correctly

To run tests run

```bash
cd backend
python -m pytest -q
```
and you will see something like this.
![3](https://github.com/shovonSharma/speech-transcriber/blob/main/3.png)

### Limitation

Vosk’s lightweight models (<40 Mb) prioritize speed and CPU efficiency over raw accuracy. While not as precise as Whisper (especially in noisy conditions or with heavy accents), the small English model used here delivers **more than enough accuracy for clear speech** — with the huge advantage of **real-time performance on CPU, near-instant transcription and full offline/privacy support**.
