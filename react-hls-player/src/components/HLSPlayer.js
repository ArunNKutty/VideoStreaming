import React, { useState, useRef, useEffect } from 'react';
import Hls from 'hls.js';
import './HLSPlayer.css';

const HLSPlayer = () => {
  const [hlsUrl, setHlsUrl] = useState('');
  const [currentUrl, setCurrentUrl] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [hlsInstance, setHlsInstance] = useState(null);
  
  const videoRef = useRef(null);

  // Sample HLS URL for testing (updated for new API structure)
  const sampleUrl = 'http://localhost:8080/api/v1/videos/a0692aec-f0f2-4922-86b0-cac1790548b6/hls/index.m3u8';

  useEffect(() => {
    // Cleanup HLS instance on component unmount
    return () => {
      if (hlsInstance) {
        hlsInstance.destroy();
      }
    };
  }, [hlsInstance]);

  const handleUrlChange = (e) => {
    setHlsUrl(e.target.value);
    setError('');
  };

  const loadAndPlay = async () => {
    if (!hlsUrl.trim()) {
      setError('Please enter a valid HLS URL');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const video = videoRef.current;
      
      if (!video) {
        throw new Error('Video element not found');
      }

      // Destroy existing HLS instance
      if (hlsInstance) {
        hlsInstance.destroy();
      }

      if (Hls.isSupported()) {
        // Use hls.js for browsers that support Media Source Extensions
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 90,
        });

        hls.loadSource(hlsUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          console.log('Manifest loaded successfully');
          setCurrentUrl(hlsUrl);
          setIsLoading(false);
          
          // Auto-play the video
          video.play().then(() => {
            setIsPlaying(true);
          }).catch((err) => {
            console.log('Auto-play prevented:', err);
            setIsPlaying(false);
          });
        });

        hls.on(Hls.Events.ERROR, (event, data) => {
          console.error('HLS Error:', data);
          setIsLoading(false);
          
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                setError('Network error: Unable to load the stream. Please check the URL and try again.');
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                setError('Media error: There was a problem with the video format.');
                hls.recoverMediaError();
                break;
              default:
                setError(`Fatal error: ${data.details}`);
                break;
            }
          }
        });

        setHlsInstance(hls);

      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (mainly Safari)
        video.src = hlsUrl;
        setCurrentUrl(hlsUrl);
        setIsLoading(false);
        
        video.addEventListener('loadedmetadata', () => {
          video.play().then(() => {
            setIsPlaying(true);
          }).catch((err) => {
            console.log('Auto-play prevented:', err);
            setIsPlaying(false);
          });
        });

        video.addEventListener('error', (e) => {
          setError('Error loading video. Please check the HLS URL.');
          setIsLoading(false);
        });

      } else {
        throw new Error('Your browser does not support HLS playback.');
      }

    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video || !currentUrl) return;

    if (video.paused) {
      video.play().then(() => {
        setIsPlaying(true);
      }).catch((err) => {
        setError('Unable to play video: ' + err.message);
      });
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  const handleVideoEnded = () => {
    setIsPlaying(false);
  };

  const handleVideoPause = () => {
    setIsPlaying(false);
  };

  const handleVideoPlay = () => {
    setIsPlaying(true);
  };

  const fillSampleUrl = () => {
    setHlsUrl(sampleUrl);
    setError('');
  };

  return (
    <div className="hls-player">
      <div className="player-container">
        <div className="controls-section">
          <div className="url-input-section">
            <label htmlFor="hls-url">HLS Stream URL:</label>
            <div className="input-group">
              <input
                id="hls-url"
                type="url"
                value={hlsUrl}
                onChange={handleUrlChange}
                placeholder="https://example.com/path/to/playlist.m3u8"
                className="url-input"
              />
              <button 
                onClick={fillSampleUrl}
                className="sample-btn"
                type="button"
              >
                Sample URL
              </button>
            </div>
          </div>

          <div className="player-controls">
            <button
              onClick={loadAndPlay}
              disabled={isLoading || !hlsUrl.trim()}
              className="load-btn"
            >
              {isLoading ? 'Loading...' : 'Load Stream'}
            </button>
            
            {currentUrl && (
              <button
                onClick={togglePlayPause}
                className="play-pause-btn"
                disabled={isLoading}
              >
                {isPlaying ? '⏸️ Pause' : '▶️ Play'}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className="video-container">
          <video
            ref={videoRef}
            controls
            muted
            onEnded={handleVideoEnded}
            onPause={handleVideoPause}
            onPlay={handleVideoPlay}
            className="video-player"
          >
            Your browser does not support the video tag.
          </video>
          
          {!currentUrl && (
            <div className="video-placeholder">
              <p>Enter an HLS URL above and click "Load Stream" to start playing</p>
            </div>
          )}
        </div>

        {currentUrl && (
          <div className="current-stream">
            <strong>Current Stream:</strong> {currentUrl}
          </div>
        )}
      </div>
    </div>
  );
};

export default HLSPlayer; 