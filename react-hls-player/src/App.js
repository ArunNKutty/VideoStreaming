import React from 'react';
import './App.css';
import HLSPlayer from './components/HLSPlayer';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>React HLS Video Player</h1>
        <p>Enter an HLS URL to stream video content</p>
      </header>
      <main className="App-main">
        <HLSPlayer />
      </main>
    </div>
  );
}

export default App; 