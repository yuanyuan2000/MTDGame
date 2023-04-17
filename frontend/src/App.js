import './App.css';
import NetworkGraph from './components/NetworkGraph';
import React, { useEffect, useState } from 'react';
import axios from 'axios';

// Define a prefix for the API URL
var prefix = "http://localhost:8000"

function App() {
  // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
  const [isGameStarted, setIsGameStarted] = useState(false);

  useEffect(() => {
    const startGame = async () => {
      try {
        const response = await axios.get(prefix + '/api/start_game/');
        console.log(response.data.message);
        setIsGameStarted(true);
      } catch (error) {
        console.error('Error starting game:', error);
      }
    };
    startGame();
  }, []);

  return (
    <div className="App" style={{ width: '100%', height: '800px' }} >
      <h1>Network Topology</h1>
      {isGameStarted && <NetworkGraph prefix={prefix} />}
    </div>
  );
}

export default App;
