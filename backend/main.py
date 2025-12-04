from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSessionType
from models import Base, Session
from vosk import Model, KaldiRecognizer
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from database import DBSession, engine
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load VOSK model
try:
    vosk_model = Model("model/vosk-model-small-en-us-0.15")
    logger.info("VOSK model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load VOSK model: {e}")
    raise

def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

@app.websocket("/ws/transcribe")
async def websocket_endpoint(ws: WebSocket, db: DBSessionType = Depends(get_db)):
    await ws.accept()
    logger.info("WebSocket connection accepted")

    
    try:
        # Create the transcription session record
        transcription_session = Session(start_ts=datetime.now(timezone.utc))
        db.add(transcription_session)
        db.commit()
        db.refresh(transcription_session)
        logger.info(f"Created DB session ID: {transcription_session.id}")

        recognizer = KaldiRecognizer(vosk_model, 16000)
        recognizer.SetWords(True)

        start_time = time.time()
        full_transcript = ""

        await ws.send_text(json.dumps({"type": "info", "message": "Ready"}))

        while True:
            data = await ws.receive_bytes()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    full_transcript += (" " + text) if full_transcript else text
                    await ws.send_text(json.dumps({"type": "final", "text": text}))
            else:
                partial = json.loads(recognizer.PartialResult()).get("partial", "")
                if partial:
                    await ws.send_text(json.dumps({"type": "partial", "text": partial}))

    except WebSocketDisconnect:
        logger.info("Client disconnected – finalizing")

        # Get any remaining final result
        final_res = json.loads(recognizer.FinalResult())
        final_text = final_res.get("text", "")
        if final_text:
            full_transcript += (" " + final_text) if full_transcript else final_text

        duration = int(time.time() - start_time)
        word_count = len(full_transcript.split())

        # Save everything using the injected db session
        transcription_session.end_ts = datetime.now(timezone.utc)
        transcription_session.duration = duration
        transcription_session.word_count = word_count
        transcription_session.transcript = full_transcript.strip()

        db.commit()
        logger.info(f"Session {transcription_session.id} saved – {word_count} words, {duration}s")

    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        db.rollback()  
        raise


@app.get("/sessions")
def get_sessions(db: DBSessionType = Depends(get_db)):
    all_sessions = db.query(Session).order_by(Session.start_ts.desc()).all()
    return [{
        "id": s.id,
        "start": s.start_ts.isoformat() if s.start_ts else None,
        "end": s.end_ts.isoformat() if s.end_ts else None,
        "words": s.word_count,
        "duration": s.duration
    } for s in all_sessions]


@app.get("/sessions/{session_id}")
def get_session(session_id: int, db: DBSessionType = Depends(get_db)):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": s.id,
        "start": s.start_ts.isoformat() if s.start_ts else None,
        "end": s.end_ts.isoformat() if s.end_ts else None,
        "duration": s.duration,
        "word_count": s.word_count,
        "transcript": s.transcript
    }


@app.get("/")
def root():
    return {"status": "Real-Time Transcription API", "vosk_loaded": vosk_model is not None}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    import sqlite3
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, start_ts, end_ts, duration, word_count, 
               length(transcript) as chars, 
               substr(transcript, 1, 150) || '...' as preview 
        FROM sessions 
        ORDER BY start_ts DESC
    """)
    rows = c.fetchall()
    conn.close()

    html = """
    <html>
        <head>
            <title>Vosk Transcriber — Admin</title>
            <meta charset="utf-8">
            <style>
                body {font-family: system-ui, sans-serif; margin: 40px; background: #f8f9fa;}
                table {width: 100%; border-collapse: collapse; margin-top: 20px;}
                th, td {padding: 12px; text-align: left; border-bottom: 1px solid #ddd;}
                th {background: #007bff; color: white;}
                tr:hover {background: #f1f1f1;}
                .preview {font-family: monospace; color: #333;}
                h1 {color: #007bff;}
            </style>
        </head>
        <body>
            <h1>Real-Time Transcription Sessions</h1>
            <p><strong>Total sessions:</strong> """ + str(len(rows)) + """</p>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Started</th>
                    <th>Ended</th>
                    <th>Duration</th>
                    <th>Words</th>
                    <th>Chars</th>
                    <th>Preview</th>
                </tr>
    """

    for row in rows:
        html += f"""
                <tr>
                    <td><a href="/sessions/{row['id']}" target="_blank">#{row['id']}</a></td>
                    <td>{row['start_ts']}</td>
                    <td>{row['end_ts'] or '—'}</td>
                    <td>{row['duration'] or '—'}s</td>
                    <td>{row['word_count'] or 0}</td>
                    <td>{row['chars']}</td>
                    <td class="preview">{row['preview']}</td>
                </tr>
        """

    html += """
            </table>
            <hr>
            <small>Refresh page to see new sessions • <a href="/">API root</a></small>
        </body>
    </html>
    """
    return HTMLResponse(html)


