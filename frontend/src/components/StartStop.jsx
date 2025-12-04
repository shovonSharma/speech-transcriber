export default function StartStop({ start, stop, isRecording }) {
  return (
    <div style={{ marginBottom: "20px" }}>
      <button 
        onClick={start} 
        disabled={isRecording}
        style={{ 
          marginRight: "10px", 
          background: isRecording ? "#ccc" : "green", 
          color: "white", 
          padding: "10px 20px",
          border: "none",
          borderRadius: "5px",
          cursor: isRecording ? "not-allowed" : "pointer",
          fontSize: "16px"
        }}
      >
        {isRecording ? "RECORDING..." : "START RECORDING"}
      </button>
      <button 
        onClick={stop}
        disabled={!isRecording}
        style={{ 
          background: !isRecording ? "#ccc" : "red", 
          color: "white", 
          padding: "10px 20px",
          border: "none",
          borderRadius: "5px",
          cursor: !isRecording ? "not-allowed" : "pointer",
          fontSize: "16px"
        }}
      >
        STOP RECORDING
      </button>
    </div>
  );
}