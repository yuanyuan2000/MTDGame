import './App.css';
import NetworkGraph from './components/NetworkGraph';
import Terminal from './components/Terminal';
import React, { useEffect, useState } from 'react';
import axios from 'axios';

// Define a prefix for the API URL
var prefix = "http://localhost:8000"

function App() {
  // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
  const [isGameStarted, setIsGameStarted] = useState(false);
  // command is a terminal state variable, when it is changed the terminal is updated
  const [command, setCommand] = useState(null);

  useEffect(() => {
    const startGame = async () => {
      try {
        const response = await axios.get(prefix + '/api/start_game/');
        console.log('/api/start_game response:', response.data.message);
        setIsGameStarted(true);
      } catch (error) {
        console.error('Error starting game:', error);
      }
    };
    startGame();
  }, []);

  const handleNodeClick = (ip) => {
    setCommand(`Node IP: ${ip}`);
  };

  return (
    <div className="App">
      <div className="main-container" style={{width: '70%'}}>
        <h1>MTD Multi-Player Game</h1>
        <div className="network-graph-container" style={{width: '100%', height: '70vh'}}>
          {isGameStarted && <NetworkGraph prefix={prefix}  handleNodeClick={handleNodeClick} />}
        </div>
        <div
          className="terminal-wrapper"
          style={{
            position: 'fixed',
            right: 0, // Set the desired distance from the right edge
            bottom: '5%', // Set the desired distance from the bottom edge
            zIndex: 1000, // Ensure the terminal is on top
            width: '30%', // Set the desired width
            height: '90%', // Set the desired height
          }}
        >
          <div className="terminal-container" style={{ backgroundColor: '#2d2d2d', width: '100%', height: '100%'}}>
          <Terminal command={command} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
