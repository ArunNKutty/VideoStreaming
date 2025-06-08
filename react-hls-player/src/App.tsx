import React, { useState } from 'react';
import './App.css';
import HLSPlayer from './components/HLSPlayer';
import VideoScheduler from './components/VideoScheduler';

type ViewType = 'player' | 'scheduler';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('player');

  const handleViewChange = (view: ViewType): void => {
    setCurrentView(view);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎬 Video Platform</h1>
        <p>Stream videos and schedule email notifications</p>
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${currentView === 'player' ? 'active' : ''}`}
            onClick={() => handleViewChange('player')}
            type="button"
          >
            🎥 Video Player
          </button>
          <button
            className={`nav-tab ${currentView === 'scheduler' ? 'active' : ''}`}
            onClick={() => handleViewChange('scheduler')}
            type="button"
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
};

export default App;