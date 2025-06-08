import React, { useState } from 'react';
import './App.css';
import HLSPlayer from './components/HLSPlayer';
import VideoScheduler from './components/VideoScheduler';

function App() {
  const [currentView, setCurrentView] = useState('player');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎬 Video Platform</h1>
        <p>Stream videos and schedule email notifications</p>
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${currentView === 'player' ? 'active' : ''}`}
            onClick={() => setCurrentView('player')}
          >
            🎥 Video Player
          </button>
          <button
            className={`nav-tab ${currentView === 'scheduler' ? 'active' : ''}`}
            onClick={() => setCurrentView('scheduler')}
          >
            📧 Email Scheduler
          </button>
        </nav>
      </header>
      <main className="App-main">
        {currentView === 'player' ? <HLSPlayer /> : <VideoScheduler />}
      </main>
    </div>
  );
}

export default App; 