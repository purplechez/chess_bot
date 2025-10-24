import { useState } from 'react';

function App() {
  const [url, setUrl] = useState('https://example.com');
  const [input, setInput] = useState(url);

  const handleGo = () => setUrl(input);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 8, background: "#222", color: "#fff" }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          style={{ width: "70%" }}
        />
        <button onClick={handleGo} style={{ marginLeft: 8 }}>Go</button>
      </div>
      <iframe
        title="Embedded Browser"
        src={url}
        style={{ flex: 1, width: "100%", border: "none" }}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
}

export default App;