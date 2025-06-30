import React from 'react';
import './App.css';
import HLSPlayer from './components/HLSPlayer';

const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <h1>🎬 Video Platform</h1>
        <p>Upload and stream HLS videos</p>
      </header>
      <main className="App-main">
        <HLSPlayer />
      </main>
    </div>
  );
};

export default App;