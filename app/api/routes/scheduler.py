"""
Video scheduling API endpoints
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.models.scheduler import (
    VideoSchedule, ScheduleCreateRequest, ScheduleUpdateRequest,
    ScheduleListResponse, CalendarEvent
)
from app.services.scheduler_service import scheduler_service

router = APIRouter(tags=["scheduler"])


@router.post("/schedules", response_model=VideoSchedule)
async def create_schedule(request: ScheduleCreateRequest):
    """Create a new video email schedule"""
    try:
        schedule = await scheduler_service.create_schedule(request)
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    """List all video schedules"""
    result = scheduler_service.list_schedules(page=page, per_page=per_page)
    return ScheduleListResponse(**result)


@router.get("/schedules/{schedule_id}", response_model=VideoSchedule)
async def get_schedule(schedule_id: str):
    """Get a specific schedule by ID"""
    schedule = scheduler_service.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/schedules/{schedule_id}", response_model=VideoSchedule)
async def update_schedule(schedule_id: str, request: ScheduleUpdateRequest):
    """Update an existing schedule"""
    try:
        schedule = await scheduler_service.update_schedule(schedule_id, request)
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule"""
    success = await scheduler_service.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted successfully"}


@router.get("/calendar/events", response_model=List[CalendarEvent])
async def get_calendar_events(
    start: Optional[str] = Query(None, description="Start date for calendar view"),
    end: Optional[str] = Query(None, description="End date for calendar view")
):
    """Get calendar events for the scheduler"""
    try:
        if start:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if end:
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            end_dt = start_dt + timedelta(days=30)  # Default to 30 days
    except ValueError:
        # Fallback to default dates if parsing fails
        start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=30)

    events = scheduler_service.get_calendar_events(start_dt, end_dt)
    return events


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_view():
    """Serve the calendar interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Scheduler Calendar</title>
        <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #2c3e50;
                margin: 0 0 10px 0;
                font-size: 28px;
            }
            .header p {
                color: #7f8c8d;
                margin: 0;
            }
            .controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
                gap: 15px;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                text-decoration: none;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .btn-secondary {
                background: #6c757d;
            }
            #calendar {
                margin-top: 20px;
            }
            .fc-event {
                border: none !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border-radius: 4px !important;
            }
            .fc-event:hover {
                opacity: 0.8;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #667eea;
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
            .stat-label {
                color: #7f8c8d;
                font-size: 14px;
            }
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }
            .modal-content {
                background-color: white;
                margin: 5% auto;
                padding: 30px;
                border-radius: 12px;
                width: 90%;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            .close:hover {
                color: #000;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #2c3e50;
            }
            .form-group input,
            .form-group select,
            .form-group textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                box-sizing: border-box;
            }
            .form-group textarea {
                height: 80px;
                resize: vertical;
            }
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            @media (max-width: 768px) {
                .form-row {
                    grid-template-columns: 1fr;
                }
                .controls {
                    flex-direction: column;
                    align-items: stretch;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Video Scheduler Calendar</h1>
                <p>Manage your video email schedules with ease</p>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalSchedules">0</div>
                    <div class="stat-label">Total Schedules</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="activeSchedules">0</div>
                    <div class="stat-label">Active Schedules</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="emailsSent">0</div>
                    <div class="stat-label">Emails Sent</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="upcomingEvents">0</div>
                    <div class="stat-label">Upcoming Events</div>
                </div>
            </div>
            
            <div class="controls">
                <div>
                    <button class="btn" onclick="openScheduleModal()">📧 New Schedule</button>
                    <button class="btn btn-secondary" onclick="refreshCalendar()">🔄 Refresh</button>
                </div>
                <div>
                    <a href="/api/v1/schedules" class="btn btn-secondary" target="_blank">📋 View All Schedules</a>
                </div>
            </div>
            
            <div id="calendar"></div>
        </div>
        
        <!-- Schedule Modal -->
        <div id="scheduleModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeScheduleModal()">&times;</span>
                <h2>📧 Create New Schedule</h2>
                <form id="scheduleForm">
                    <div class="form-group">
                        <label for="videoId">Video ID *</label>
                        <input type="text" id="videoId" name="videoId" required 
                               placeholder="Enter video asset ID">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="recipientEmail">Recipient Email *</label>
                            <input type="email" id="recipientEmail" name="recipientEmail" required 
                                   placeholder="recipient@example.com">
                        </div>
                        <div class="form-group">
                            <label for="recipientName">Recipient Name</label>
                            <input type="text" id="recipientName" name="recipientName" 
                                   placeholder="John Doe">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="subject">Email Subject *</label>
                        <input type="text" id="subject" name="subject" required 
                               placeholder="Your video is ready!">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="scheduledDate">Scheduled Date & Time *</label>
                            <input type="datetime-local" id="scheduledDate" name="scheduledDate" required>
                        </div>
                        <div class="form-group">
                            <label for="frequency">Frequency</label>
                            <select id="frequency" name="frequency">
                                <option value="once">Once</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="template">Email Template</label>
                            <select id="template" name="template">
                                <option value="standard">Standard</option>
                                <option value="premium">Premium</option>
                                <option value="minimal">Minimal</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="senderName">Sender Name</label>
                            <input type="text" id="senderName" name="senderName" 
                                   placeholder="Video Platform" value="Video Platform">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="message">Custom Message</label>
                        <textarea id="message" name="message" 
                                  placeholder="Add a personal message (optional)"></textarea>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="includeThumbnail" name="includeThumbnail" checked>
                                Include Thumbnail
                            </label>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="includeDuration" name="includeDuration" checked>
                                Include Duration
                            </label>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <button type="submit" class="btn">📅 Create Schedule</button>
                        <button type="button" class="btn btn-secondary" onclick="closeScheduleModal()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            let calendar;
            
            document.addEventListener('DOMContentLoaded', function() {
                initializeCalendar();
                loadStats();
                
                // Set default datetime to now + 1 hour
                const now = new Date();
                now.setHours(now.getHours() + 1);
                document.getElementById('scheduledDate').value = now.toISOString().slice(0, 16);
            });
            
            function initializeCalendar() {
                const calendarEl = document.getElementById('calendar');
                calendar = new FullCalendar.Calendar(calendarEl, {
                    initialView: 'dayGridMonth',
                    headerToolbar: {
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,timeGridDay'
                    },
                    events: function(fetchInfo, successCallback, failureCallback) {
                        fetch(`/api/v1/calendar/events?start=${fetchInfo.startStr}&end=${fetchInfo.endStr}`)
                            .then(response => response.json())
                            .then(data => {
                                const events = data.map(event => ({
                                    id: event.id,
                                    title: event.title,
                                    start: event.start,
                                    end: event.end,
                                    description: event.description,
                                    extendedProps: {
                                        videoId: event.video_id,
                                        recipientEmail: event.recipient_email,
                                        status: event.status,
                                        frequency: event.frequency
                                    }
                                }));
                                successCallback(events);
                            })
                            .catch(error => {
                                console.error('Error loading events:', error);
                                failureCallback(error);
                            });
                    },
                    eventClick: function(info) {
                        alert(`Event: ${info.event.title}\\nRecipient: ${info.event.extendedProps.recipientEmail}\\nVideo ID: ${info.event.extendedProps.videoId}`);
                    }
                });
                calendar.render();
            }
            
            function loadStats() {
                fetch('/api/v1/schedules')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('totalSchedules').textContent = data.total;
                        
                        const activeSchedules = data.schedules.filter(s => s.status === 'active').length;
                        document.getElementById('activeSchedules').textContent = activeSchedules;
                        
                        const emailsSent = data.schedules.reduce((sum, s) => sum + s.send_count, 0);
                        document.getElementById('emailsSent').textContent = emailsSent;
                        
                        // Calculate upcoming events (simplified)
                        document.getElementById('upcomingEvents').textContent = activeSchedules;
                    })
                    .catch(error => console.error('Error loading stats:', error));
            }
            
            function openScheduleModal() {
                document.getElementById('scheduleModal').style.display = 'block';
            }
            
            function closeScheduleModal() {
                document.getElementById('scheduleModal').style.display = 'none';
                document.getElementById('scheduleForm').reset();
            }
            
            function refreshCalendar() {
                calendar.refetchEvents();
                loadStats();
            }
            
            document.getElementById('scheduleForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const scheduleData = {
                    video_id: formData.get('videoId'),
                    recipient_email: formData.get('recipientEmail'),
                    recipient_name: formData.get('recipientName') || null,
                    sender_name: formData.get('senderName') || 'Video Platform',
                    scheduled_date: formData.get('scheduledDate'),
                    frequency: formData.get('frequency'),
                    subject: formData.get('subject'),
                    message: formData.get('message') || null,
                    template: formData.get('template'),
                    include_thumbnail: formData.has('includeThumbnail'),
                    include_duration: formData.has('includeDuration')
                };
                
                fetch('/api/v1/schedules', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(scheduleData)
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => Promise.reject(err));
                    }
                    return response.json();
                })
                .then(data => {
                    alert('Schedule created successfully!');
                    closeScheduleModal();
                    refreshCalendar();
                })
                .catch(error => {
                    console.error('Error creating schedule:', error);
                    alert('Error creating schedule: ' + (error.detail || 'Unknown error'));
                });
            });
            
            // Close modal when clicking outside
            window.onclick = function(event) {
                const modal = document.getElementById('scheduleModal');
                if (event.target === modal) {
                    closeScheduleModal();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
