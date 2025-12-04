export default function FinalTranscript({ text }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: "10px", marginBottom: "20px" }}>
      <h3>Final Transcript</h3>
      <p style={{ fontSize: "18px", minHeight: "40px", whiteSpace: "pre-wrap" }}>{text}</p>
    </div>
  );
}
