import { useRef, useState } from "react";
import StartStop from "./components/StartStop";
import LivePartial from "./components/LivePartial";
import FinalTranscript from "./components/FinalTranscript";
import Stats from "./components/Stats";

export default function App() {
  const [partial, setPartial] = useState("");
  const [finalText, setFinalText] = useState("");
  const [wordCount, setWordCount] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Ready");
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const startTimeRef = useRef(null);
  const audioBufferRef = useRef([]);

  function floatTo16BitPCM(float32Array) {
    const buffer = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      buffer[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return buffer;
  }

  function downsampleBuffer(buffer, inputRate, outputRate) {
    if (outputRate === inputRate) {
      return buffer;
    }
    const sampleRateRatio = inputRate / outputRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    
    let offsetResult = 0;
    let offsetBuffer = 0;
    
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    
    return result;
  }

  async function startRecording() {
    try {
      setStatus("Connecting...");
      setFinalText("");
      setPartial("");
      setWordCount(0);
      setDuration(0);
      
      // Create WebSocket connection
      const ws = new WebSocket("ws://localhost:8000/ws/transcribe");
      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setStatus("Recording...");
      };

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          console.log("📩 Received:", msg);
          
          if (msg.type === "partial") {
            setPartial(msg.text);
          } else if (msg.type === "final") {
            setFinalText((prev) => {
              const newText = prev ? prev + " " + msg.text : msg.text;
              return newText;
            });
            setPartial(""); // Clear partial after final
          } else if (msg.type === "info") {
            console.log("ℹ️ Info:", msg.message);
          }
        } catch (err) {
          console.error("❌ Error parsing message:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("❌ WebSocket error:", err);
        setStatus("Error: Connection failed");
      };

      ws.onclose = () => {
        console.log("🔌 WebSocket closed");
        setStatus("Stopped");
      };

      wsRef.current = ws;

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000  // Request 16kHz if possible
        } 
      });
      
      streamRef.current = stream;
      console.log("🎤 Microphone access granted");

      // Create audio context
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      const inputSampleRate = audioContext.sampleRate;
      console.log(`🔊 Audio context sample rate: ${inputSampleRate}Hz`);

      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;

      // Use larger buffer for more reliable processing
      const bufferSize = 8192; // Increased from 4096
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      let totalBytesSent = 0;

      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }

        const inputData = e.inputBuffer.getChannelData(0);
        
        // Downsample to 16kHz
        const downsampled = downsampleBuffer(inputData, inputSampleRate, 16000);
        
        // Convert to 16-bit PCM
        const pcm16 = floatTo16BitPCM(downsampled);
        
        // Send to backend
        try {
          wsRef.current.send(pcm16.buffer);
          totalBytesSent += pcm16.buffer.byteLength;
          
          if (totalBytesSent % 100000 < pcm16.buffer.byteLength) {
            console.log(`📤 Sent ${Math.round(totalBytesSent / 1000)}KB of audio`);
          }
        } catch (err) {
          console.error("❌ Error sending audio:", err);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      startTimeRef.current = Date.now();
      setIsRecording(true);
      
    } catch (err) {
      console.error("❌ Error starting recording:", err);
      setStatus(`Error: ${err.message}`);
      stopRecording();
    }
  }

  function stopRecording() {
    console.log("🛑 Stopping recording...");
    
    // Disconnect audio processing
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Stop microphone
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Calculate duration
    if (startTimeRef.current) {
      const durationMs = Date.now() - startTimeRef.current;
      setDuration(Math.round(durationMs / 1000));
      startTimeRef.current = null;
    }

    // Update word count from final text
    setWordCount((prevFinalText) => {
      return finalText.split(/\s+/).filter(Boolean).length;
    });
    
    setPartial("");
    setIsRecording(false);
    setStatus("Stopped");
  }

  return (
    <div style={{ margin: "20px", fontFamily: "sans-serif", maxWidth: "800px" }}>
      <h2>🎙️ REAL-TIME SPEECH TRANSCRIBER</h2>
      
      <div style={{ 
        padding: "10px", 
        marginBottom: "20px", 
        background: isRecording ? "#d4edda" : "#f8f9fa",
        border: "1px solid #ccc",
        borderRadius: "5px"
      }}>
        <strong>Status:</strong> {status}
      </div>
      
      <StartStop 
        start={startRecording} 
        stop={stopRecording} 
        isRecording={isRecording}
      />
      
      <LivePartial text={partial} />
      <FinalTranscript text={finalText} />
      <Stats wordCount={wordCount} duration={duration} />
      
      
    </div>
  );
}