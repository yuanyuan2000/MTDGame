import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import GameSelection from "./components/GameSelection";
import DefenderGame from "./components/defender/Game";
import AttackerGame from "./components/attacker/Game";
import React, { createContext } from 'react';

export const UrlPrefixContext = createContext();

function App() {
  // const prefix = "http://localhost:8000";
  // const prefix = "http://192.168.137.23:8000";
  // const prefix = "http://192.168.43.15:8000";
  const prefix = "http://34.151.70.209:8000"
  
  return (
    <UrlPrefixContext.Provider value={prefix}>
      <Router>
        <Routes>
          <Route exact path="/" element={<GameSelection />} />
          <Route path="/game/defender/:roomId" element={<DefenderGame />} />
          <Route path="/game/attacker/:roomId" element={<AttackerGame />} />
        </Routes>
      </Router>
    </UrlPrefixContext.Provider>
  );
}

export default App;
