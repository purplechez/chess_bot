import React, { useState } from 'react';
import Chessboard from "react-chessboard";
import { Chess } from "chess.js";

function App() {
  const [game, setGame] = useState(new Chess());
  const [bestMove, setBestMove] = useState(null);
  const [score, setScore] = useState(null);

  async function getBestMove() {
    const fen = game.fen();
    const res = await fetch("http://localhost:8000/bestmove/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fen })
    });
    const data = await res.json();
    setBestMove(data.bestmove);
    setScore(data.score);
  }

  function onDrop(sourceSquare, targetSquare) {
    const move = game.move({ from: sourceSquare, to: targetSquare, promotion: "q" });
    if (move === null) return false;
    setGame(new Chess(game.fen()));
    setBestMove(null);
    setScore(null);
    return true;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <h2>Chess Analysis Board</h2>
      <Chessboard position={game.fen()} onPieceDrop={onDrop} />
      <button onClick={getBestMove} style={{marginTop: 16}}>Suggest Best Move</button>
      {bestMove && (
        <div style={{marginTop: 16}}>
          <b>Best Move:</b> {bestMove}<br />
          <b>Evaluation:</b> {score > 9000 ? "Checkmate" : score}
        </div>
      )}
    </div>
  );
}

export default App;