"""
Scheduler-related Pydantic models
"""
from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class FrequencyType(str, Enum):
    """Email frequency types"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduleStatus(str, Enum):
    """Schedule status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailTemplate(str, Enum):
    """Email template types"""
    STANDARD = "standard"
    PREMIUM = "premium"
    MINIMAL = "minimal"
    CUSTOM = "custom"


class VideoSchedule(BaseModel):
    """Video schedule model"""
    id: Optional[str] = Field(default=None, description="Schedule ID")
    video_id: str = Field(..., description="Video asset ID")
    video_title: str = Field(..., description="Video title")
    video_url: str = Field(..., description="Video streaming URL")
    
    # Recipient information
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name")
    sender_name: Optional[str] = Field(default="Video Platform", description="Sender name")
    
    # Schedule information
    scheduled_date: datetime = Field(..., description="Scheduled date and time")
    frequency: FrequencyType = Field(default=FrequencyType.ONCE, description="Email frequency")
    custom_cron: Optional[str] = Field(default=None, description="Custom cron expression for frequency")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    
    # Email content
    subject: str = Field(..., description="Email subject")
    message: Optional[str] = Field(default=None, description="Custom message")
    template: EmailTemplate = Field(default=EmailTemplate.STANDARD, description="Email template")
    
    # Schedule metadata
    status: ScheduleStatus = Field(default=ScheduleStatus.ACTIVE, description="Schedule status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    last_sent: Optional[datetime] = Field(default=None, description="Last email sent timestamp")
    next_send: Optional[datetime] = Field(default=None, description="Next scheduled send time")
    send_count: int = Field(default=0, description="Number of emails sent")
    
    # Additional options
    include_thumbnail: bool = Field(default=True, description="Include video thumbnail")
    include_duration: bool = Field(default=True, description="Include video duration")
    auto_expire: Optional[datetime] = Field(default=None, description="Auto-expire date")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScheduleCreateRequest(BaseModel):
    """Request model for creating a schedule"""
    video_id: str = Field(..., description="Video asset ID")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name")
    sender_name: Optional[str] = Field(default="Video Platform", description="Sender name")
    
    scheduled_date: datetime = Field(..., description="Scheduled date and time")
    frequency: FrequencyType = Field(default=FrequencyType.ONCE, description="Email frequency")
    custom_cron: Optional[str] = Field(default=None, description="Custom cron expression")
    timezone: str = Field(default="UTC", description="Timezone")
    
    subject: str = Field(..., description="Email subject")
    message: Optional[str] = Field(default=None, description="Custom message")
    template: EmailTemplate = Field(default=EmailTemplate.STANDARD, description="Email template")
    
    include_thumbnail: bool = Field(default=True, description="Include video thumbnail")
    include_duration: bool = Field(default=True, description="Include video duration")
    auto_expire: Optional[datetime] = Field(default=None, description="Auto-expire date")


class ScheduleUpdateRequest(BaseModel):
    """Request model for updating a schedule"""
    recipient_email: Optional[EmailStr] = Field(default=None, description="Recipient email address")
    recipient_name: Optional[str] = Field(default=None, description="Recipient name")
    sender_name: Optional[str] = Field(default=None, description="Sender name")
    
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled date and time")
    frequency: Optional[FrequencyType] = Field(default=None, description="Email frequency")
    custom_cron: Optional[str] = Field(default=None, description="Custom cron expression")
    timezone: Optional[str] = Field(default=None, description="Timezone")
    
    subject: Optional[str] = Field(default=None, description="Email subject")
    message: Optional[str] = Field(default=None, description="Custom message")
    template: Optional[EmailTemplate] = Field(default=None, description="Email template")
    
    status: Optional[ScheduleStatus] = Field(default=None, description="Schedule status")
    include_thumbnail: Optional[bool] = Field(default=None, description="Include video thumbnail")
    include_duration: Optional[bool] = Field(default=None, description="Include video duration")
    auto_expire: Optional[datetime] = Field(default=None, description="Auto-expire date")


class ScheduleListResponse(BaseModel):
    """Response model for schedule list"""
    schedules: List[VideoSchedule] = Field(..., description="List of schedules")
    total: int = Field(..., description="Total number of schedules")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=10, description="Items per page")


class EmailSendResult(BaseModel):
    """Email send result model"""
    schedule_id: str = Field(..., description="Schedule ID")
    success: bool = Field(..., description="Send success status")
    message_id: Optional[str] = Field(default=None, description="Email message ID")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    sent_at: datetime = Field(default_factory=datetime.now, description="Send timestamp")


class CalendarEvent(BaseModel):
    """Calendar event model for frontend"""
    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    start: datetime = Field(..., description="Event start time")
    end: Optional[datetime] = Field(default=None, description="Event end time")
    description: Optional[str] = Field(default=None, description="Event description")
    video_id: str = Field(..., description="Associated video ID")
    recipient_email: str = Field(..., description="Recipient email")
    status: ScheduleStatus = Field(..., description="Schedule status")
    frequency: FrequencyType = Field(..., description="Frequency type")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
