import React, { useState, useEffect } from 'react';
import './VideoScheduler.css';

const VideoScheduler = () => {
    const [videos, setVideos] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        video_id: '',
        recipient_email: '',
        recipient_name: '',
        sender_name: 'Video Platform',
        scheduled_date: '',
        frequency: 'once',
        subject: '',
        message: '',
        template: 'standard',
        include_thumbnail: true,
        include_duration: true
    });

    const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8080';

    useEffect(() => {
        loadSchedules();
        // Set default datetime to now + 1 hour
        const now = new Date();
        now.setHours(now.getHours() + 1);
        setFormData(prev => ({
            ...prev,
            scheduled_date: now.toISOString().slice(0, 16)
        }));
    }, []);

    const loadSchedules = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/schedules`);
            const data = await response.json();
            setSchedules(data.schedules || []);
        } catch (error) {
            console.error('Error loading schedules:', error);
        }
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/schedules`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create schedule');
            }

            const newSchedule = await response.json();
            setSchedules(prev => [...prev, newSchedule]);
            setShowForm(false);
            setFormData({
                video_id: '',
                recipient_email: '',
                recipient_name: '',
                sender_name: 'Video Platform',
                scheduled_date: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
                frequency: 'once',
                subject: '',
                message: '',
                template: 'standard',
                include_thumbnail: true,
                include_duration: true
            });
            
            alert('Schedule created successfully!');
        } catch (error) {
            console.error('Error creating schedule:', error);
            alert('Error creating schedule: ' + error.message);
        }
    };

    const deleteSchedule = async (scheduleId) => {
        if (!window.confirm('Are you sure you want to delete this schedule?')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/v1/schedules/${scheduleId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setSchedules(prev => prev.filter(s => s.id !== scheduleId));
                alert('Schedule deleted successfully!');
            } else {
                throw new Error('Failed to delete schedule');
            }
        } catch (error) {
            console.error('Error deleting schedule:', error);
            alert('Error deleting schedule: ' + error.message);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const getStatusBadge = (status) => {
        const statusColors = {
            active: '#28a745',
            paused: '#ffc107',
            completed: '#6c757d',
            failed: '#dc3545'
        };

        return (
            <span 
                className="status-badge" 
                style={{ backgroundColor: statusColors[status] || '#6c757d' }}
            >
                {status.toUpperCase()}
            </span>
        );
    };

    const getFrequencyIcon = (frequency) => {
        const icons = {
            once: '📅',
            daily: '🔄',
            weekly: '📆',
            monthly: '🗓️',
            custom: '⚙️'
        };
        return icons[frequency] || '📅';
    };

    return (
        <div className="video-scheduler">
            <div className="scheduler-header">
                <h1>📧 Video Email Scheduler</h1>
                <p>Schedule video emails to be sent automatically</p>
                <div className="header-actions">
                    <button 
                        className="btn btn-primary"
                        onClick={() => setShowForm(true)}
                    >
                        ➕ New Schedule
                    </button>
                    <a 
                        href={`${API_BASE}/api/v1/calendar`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                    >
                        📅 Calendar View
                    </a>
                </div>
            </div>

            {/* Statistics */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-number">{schedules.length}</div>
                    <div className="stat-label">Total Schedules</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">
                        {schedules.filter(s => s.status === 'active').length}
                    </div>
                    <div className="stat-label">Active Schedules</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">
                        {schedules.reduce((sum, s) => sum + s.send_count, 0)}
                    </div>
                    <div className="stat-label">Emails Sent</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">
                        {schedules.filter(s => s.status === 'completed').length}
                    </div>
                    <div className="stat-label">Completed</div>
                </div>
            </div>

            {/* Schedule Form Modal */}
            {showForm && (
                <div className="modal-overlay" onClick={() => setShowForm(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>📧 Create New Schedule</h2>
                            <button 
                                className="close-btn"
                                onClick={() => setShowForm(false)}
                            >
                                ✕
                            </button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="schedule-form">
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Video ID *</label>
                                    <input
                                        type="text"
                                        name="video_id"
                                        value={formData.video_id}
                                        onChange={handleInputChange}
                                        placeholder="Enter video asset ID"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Email Template</label>
                                    <select
                                        name="template"
                                        value={formData.template}
                                        onChange={handleInputChange}
                                    >
                                        <option value="standard">Standard</option>
                                        <option value="premium">Premium</option>
                                        <option value="minimal">Minimal</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Recipient Email *</label>
                                    <input
                                        type="email"
                                        name="recipient_email"
                                        value={formData.recipient_email}
                                        onChange={handleInputChange}
                                        placeholder="recipient@example.com"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Recipient Name</label>
                                    <input
                                        type="text"
                                        name="recipient_name"
                                        value={formData.recipient_name}
                                        onChange={handleInputChange}
                                        placeholder="John Doe"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Email Subject *</label>
                                <input
                                    type="text"
                                    name="subject"
                                    value={formData.subject}
                                    onChange={handleInputChange}
                                    placeholder="Your video is ready!"
                                    required
                                />
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Scheduled Date & Time *</label>
                                    <input
                                        type="datetime-local"
                                        name="scheduled_date"
                                        value={formData.scheduled_date}
                                        onChange={handleInputChange}
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Frequency</label>
                                    <select
                                        name="frequency"
                                        value={formData.frequency}
                                        onChange={handleInputChange}
                                    >
                                        <option value="once">Once</option>
                                        <option value="daily">Daily</option>
                                        <option value="weekly">Weekly</option>
                                        <option value="monthly">Monthly</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Custom Message</label>
                                <textarea
                                    name="message"
                                    value={formData.message}
                                    onChange={handleInputChange}
                                    placeholder="Add a personal message (optional)"
                                    rows="3"
                                />
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Sender Name</label>
                                    <input
                                        type="text"
                                        name="sender_name"
                                        value={formData.sender_name}
                                        onChange={handleInputChange}
                                        placeholder="Video Platform"
                                    />
                                </div>
                                <div className="form-group checkbox-group">
                                    <label>
                                        <input
                                            type="checkbox"
                                            name="include_thumbnail"
                                            checked={formData.include_thumbnail}
                                            onChange={handleInputChange}
                                        />
                                        Include Thumbnail
                                    </label>
                                    <label>
                                        <input
                                            type="checkbox"
                                            name="include_duration"
                                            checked={formData.include_duration}
                                            onChange={handleInputChange}
                                        />
                                        Include Duration
                                    </label>
                                </div>
                            </div>

                            <div className="form-actions">
                                <button type="submit" className="btn btn-primary">
                                    📅 Create Schedule
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowForm(false)}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Schedules List */}
            <div className="schedules-list">
                <h2>📋 Current Schedules</h2>
                {schedules.length === 0 ? (
                    <div className="empty-state">
                        <p>No schedules created yet.</p>
                        <button 
                            className="btn btn-primary"
                            onClick={() => setShowForm(true)}
                        >
                            Create Your First Schedule
                        </button>
                    </div>
                ) : (
                    <div className="schedules-grid">
                        {schedules.map(schedule => (
                            <div key={schedule.id} className="schedule-card">
                                <div className="schedule-header">
                                    <div className="schedule-title">
                                        {getFrequencyIcon(schedule.frequency)} {schedule.video_title}
                                    </div>
                                    {getStatusBadge(schedule.status)}
                                </div>
                                
                                <div className="schedule-details">
                                    <div className="detail-row">
                                        <span className="label">📧 To:</span>
                                        <span>{schedule.recipient_email}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="label">📅 Scheduled:</span>
                                        <span>{formatDate(schedule.scheduled_date)}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="label">🔄 Frequency:</span>
                                        <span>{schedule.frequency}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span className="label">📊 Sent:</span>
                                        <span>{schedule.send_count} times</span>
                                    </div>
                                    {schedule.last_sent && (
                                        <div className="detail-row">
                                            <span className="label">⏰ Last Sent:</span>
                                            <span>{formatDate(schedule.last_sent)}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="schedule-actions">
                                    <button 
                                        className="btn btn-small btn-danger"
                                        onClick={() => deleteSchedule(schedule.id)}
                                    >
                                        🗑️ Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default VideoScheduler;
