import React, { useEffect, useRef, useState, useCallback } from 'react';
import Hls from 'hls.js';
import './MuxLikePlayer.css';

const MuxLikePlayer = ({ 
    assetId, 
    apiKey, 
    autoplay = false,
    muted = false,
    controls = true,
    width = "100%",
    height = "auto",
    onReady,
    onError,
    onAnalytics
}) => {
    const videoRef = useRef(null);
    const hlsRef = useRef(null);
    const [sessionId, setSessionId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [videoData, setVideoData] = useState(null);
    const [analytics, setAnalytics] = useState({
        playTime: 0,
        bufferingTime: 0,
        totalEvents: 0
    });

    const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

    // API helper function
    const apiCall = useCallback(async (endpoint, options = {}) => {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return response.json();
    }, [apiKey, API_BASE]);

    // Track analytics events
    const trackEvent = useCallback(async (eventType, data = {}) => {
        if (!sessionId) return;

        try {
            const eventData = {
                session_id: sessionId,
                event_type: eventType,
                data: {
                    ...data,
                    timestamp: Date.now(),
                    current_time: videoRef.current?.currentTime || 0,
                    video_duration: videoRef.current?.duration || 0,
                    playback_rate: videoRef.current?.playbackRate || 1,
                    volume: videoRef.current?.volume || 1,
                    muted: videoRef.current?.muted || false
                }
            };

            await apiCall('/v1/analytics/events', {
                method: 'POST',
                body: JSON.stringify(eventData)
            });

            setAnalytics(prev => ({
                ...prev,
                totalEvents: prev.totalEvents + 1
            }));

            if (onAnalytics) {
                onAnalytics(eventData);
            }
        } catch (error) {
            console.error('Failed to track event:', error);
        }
    }, [sessionId, apiCall, onAnalytics]);

    // Initialize video and analytics
    useEffect(() => {
        if (!assetId || !apiKey) return;

        const initializeVideo = async () => {
            try {
                setIsLoading(true);
                setError(null);

                // Get video asset details
                const asset = await apiCall(`/v1/video/assets/${assetId}`);
                setVideoData(asset);

                if (asset.status !== 'ready') {
                    setError(`Video is ${asset.status}. Please wait for processing to complete.`);
                    return;
                }

                // Create analytics session
                const session = await apiCall('/v1/analytics/sessions', {
                    method: 'POST',
                    body: JSON.stringify({
                        asset_id: assetId,
                        viewer_id: `viewer_${Date.now()}`
                    })
                });
                setSessionId(session.id);

                // Initialize HLS player
                const video = videoRef.current;
                if (!video) return;

                if (Hls.isSupported()) {
                    const hls = new Hls({
                        enableWorker: true,
                        lowLatencyMode: true,
                        backBufferLength: 90
                    });

                    hlsRef.current = hls;

                    hls.loadSource(`${API_BASE}/v1/video/assets/${assetId}/playback`);
                    hls.attachMedia(video);

                    hls.on(Hls.Events.MANIFEST_PARSED, () => {
                        setIsLoading(false);
                        if (onReady) onReady(asset);
                        trackEvent('video_ready', { 
                            duration: video.duration,
                            levels: hls.levels.length 
                        });
                    });

                    hls.on(Hls.Events.ERROR, (event, data) => {
                        console.error('HLS Error:', data);
                        if (data.fatal) {
                            setError('Failed to load video');
                            if (onError) onError(data);
                            trackEvent('error', { error: data.type, details: data.details });
                        }
                    });

                    hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
                        trackEvent('quality_change', { 
                            level: data.level,
                            bitrate: hls.levels[data.level]?.bitrate 
                        });
                    });

                } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                    // Native HLS support (Safari)
                    video.src = `${API_BASE}/v1/video/assets/${assetId}/playback`;
                    video.addEventListener('loadedmetadata', () => {
                        setIsLoading(false);
                        if (onReady) onReady(asset);
                        trackEvent('video_ready', { duration: video.duration });
                    });
                } else {
                    setError('HLS is not supported in this browser');
                }

            } catch (error) {
                console.error('Failed to initialize video:', error);
                setError(error.message);
                if (onError) onError(error);
            }
        };

        initializeVideo();

        return () => {
            if (hlsRef.current) {
                hlsRef.current.destroy();
            }
        };
    }, [assetId, apiKey, onReady, onError, apiCall, trackEvent]);

    // Video event listeners
    useEffect(() => {
        const video = videoRef.current;
        if (!video || !sessionId) return;

        const eventHandlers = {
            play: () => trackEvent('play'),
            pause: () => trackEvent('pause'),
            ended: () => trackEvent('ended'),
            seeking: () => trackEvent('seeking', { seek_to: video.currentTime }),
            seeked: () => trackEvent('seeked', { seek_to: video.currentTime }),
            waiting: () => {
                trackEvent('buffering_start');
                setAnalytics(prev => ({ ...prev, bufferingStart: Date.now() }));
            },
            canplay: () => {
                trackEvent('buffering_end');
                const bufferingStart = analytics.bufferingStart;
                if (bufferingStart) {
                    const bufferingDuration = Date.now() - bufferingStart;
                    setAnalytics(prev => ({
                        ...prev,
                        bufferingTime: prev.bufferingTime + bufferingDuration,
                        bufferingStart: null
                    }));
                }
            },
            timeupdate: () => {
                // Track play time every 10 seconds
                if (Math.floor(video.currentTime) % 10 === 0) {
                    trackEvent('heartbeat', { 
                        current_time: video.currentTime,
                        buffered_ranges: video.buffered.length
                    });
                }
            },
            volumechange: () => trackEvent('volume_change', { 
                volume: video.volume, 
                muted: video.muted 
            }),
            ratechange: () => trackEvent('playback_rate_change', { 
                playback_rate: video.playbackRate 
            }),
            error: (e) => {
                trackEvent('video_error', { 
                    error: e.target.error?.message || 'Unknown error' 
                });
                setError('Video playback error');
            }
        };

        // Add event listeners
        Object.entries(eventHandlers).forEach(([event, handler]) => {
            video.addEventListener(event, handler);
        });

        // Cleanup
        return () => {
            Object.entries(eventHandlers).forEach(([event, handler]) => {
                video.removeEventListener(event, handler);
            });
        };
    }, [sessionId, trackEvent, analytics.bufferingStart]);

    // Track session end on unmount
    useEffect(() => {
        return () => {
            if (sessionId) {
                trackEvent('session_end', {
                    total_play_time: analytics.playTime,
                    total_buffering_time: analytics.bufferingTime,
                    total_events: analytics.totalEvents
                });
            }
        };
    }, [sessionId, analytics, trackEvent]);

    if (error) {
        return (
            <div className="mux-player-error">
                <div className="error-icon">⚠️</div>
                <div className="error-message">{error}</div>
                <button 
                    className="retry-button"
                    onClick={() => window.location.reload()}
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="mux-player-container" style={{ width, height }}>
            {isLoading && (
                <div className="mux-player-loading">
                    <div className="loading-spinner"></div>
                    <div className="loading-text">Loading video...</div>
                </div>
            )}
            
            <video
                ref={videoRef}
                controls={controls}
                autoPlay={autoplay}
                muted={muted}
                className="mux-player-video"
                style={{ 
                    width: '100%', 
                    height: '100%',
                    display: isLoading ? 'none' : 'block'
                }}
                playsInline
                preload="metadata"
            />
            
            {videoData && (
                <div className="mux-player-info">
                    <div className="video-title">{videoData.filename}</div>
                    <div className="video-stats">
                        Duration: {videoData.duration ? `${Math.round(videoData.duration)}s` : 'Unknown'} | 
                        Status: {videoData.status} | 
                        Events: {analytics.totalEvents}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MuxLikePlayer;
