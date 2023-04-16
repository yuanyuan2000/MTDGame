import React from 'react';
import './App.css';
import NetworkGraph from './components/NetworkGraph';

function App() {
    return (
        <div className="App"  style={{ width: '100%', height: '800px' }} >
          <h1>Network Topology</h1>
          <NetworkGraph />
        </div>
    );
}

export default App;
