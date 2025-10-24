import React, { useState } from "react";

function App() {
  const [expr, setExpr] = useState("");
  const [result, setResult] = useState<string>("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResult("Calculating...");
    try {
      const res = await fetch("http://localhost:8000/api/eval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expr }),
      });
      const data = await res.json();
      if (data.result !== undefined) setResult(data.result);
      else setResult(`Error: ${data.error}`);
    } catch (err) {
      setResult("Network error.");
    }
  }

  return (
    <div style={{ maxWidth: 550, margin: "3rem auto", padding: 16, border: "1px solid #ccc", borderRadius: 8, fontFamily: "sans-serif" }}>
      <h2>🧮 HyperCalc Web</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input
          value={expr}
          onChange={e => setExpr(e.target.value)}
          placeholder="Enter expression, e.g., sin(pi/2) + 2"
          style={{ width: "70%", fontSize: 18, padding: 8 }}
        />
        <button type="submit" style={{ marginLeft: 8, fontSize: 18, padding: "8px 16px" }}>
          Calculate
        </button>
      </form>
      <div style={{ fontSize: 20, minHeight: 32 }}>
        {result}
      </div>
      <div style={{ marginTop: 40, color: "#888" }}>
        <b>Examples:</b> <br />
        <code>sin(pi/2)</code> <br />
        <code>2 * 3 + 4</code> <br />
        <code>exp(1)</code> <br />
        <code>log(10)</code> <br />
        <code>cos(0)</code>
      </div>
    </div>
  );
}

export default App;