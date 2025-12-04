import pytest
from fastapi.testclient import TestClient
from main import app, vosk_model  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import DBSession, engine
from models import Base, Session as TranscriptionSession

client = TestClient(app)

# Use a separate test database so real db.sqlite is untouched
TEST_DATABASE_URL = "sqlite:///test_db.sqlite"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Recreate tables in test DB
Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[DBSession] = override_get_db

# TEST-1 → Proves FastAPI starts + Vosk model loads successfully
def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Real-Time Transcription API"
    assert response.json()["vosk_loaded"] is True


# TEST-2 → Proves core real-time flow works
# WebSocket → receives audio → Vosk processes it → saves to DB → appears in /sessions

def test_create_and_list_sessions_via_websocket():
    # Simulate a short recording using WebSocket
    with client.websocket_connect("/ws/transcribe") as ws:
        # Send a tiny valid 16kHz PCM chunk (silence → Vosk returns empty)
        silence = bytes(32000)  # 1 second of silence (16kHz, 16-bit = 32000 bytes)
        ws.send_bytes(silence)
        ws.send_bytes(silence)

        # Close connection → triggers FinalResult and DB save
        ws.close()

    # Now check that a session was created
    response = client.get("/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) >= 1
    latest = sessions[0]
    assert latest["words"] == 0          # silence → 0 words
    assert latest["duration"] is not None


# TEST-3 → Proves REST API returns the full transcript + metadata correctly
def test_get_specific_session():
    # First create one via WebSocket
    with client.websocket_connect("/ws/transcribe") as ws:
        ws.send_bytes(bytes(32000))  # silence
        ws.close()

    # Get the latest session ID
    sessions = client.get("/sessions").json()
    session_id = sessions[0]["id"]

    # Fetch it
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert "transcript" in data
    assert data["word_count"] == 0