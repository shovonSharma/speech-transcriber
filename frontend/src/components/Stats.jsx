export default function Stats({ wordCount, duration }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: "10px", marginBottom: "20px" }}>
      <p><strong>Word Count:</strong> {wordCount}</p>
      <p><strong>Duration:</strong> {duration} sec</p>
    </div>
  );
}
