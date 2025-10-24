const express = require('express');
const path = require('path');
const app = express();
const PORT = 8080;

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'client', 'dist')));

// All other requests return the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'client', 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});