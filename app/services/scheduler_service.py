"""
Video scheduling service with APScheduler
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from app.models.scheduler import (
    VideoSchedule, ScheduleCreateRequest, ScheduleUpdateRequest,
    FrequencyType, ScheduleStatus, CalendarEvent
)
from app.models.video import VideoAsset
from app.services.email_service import email_service
from app.services.video_service import video_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing video email schedules"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.schedules: Dict[str, VideoSchedule] = {}  # In-memory storage (use database in production)
        self._started = False
        logger.info("Scheduler service initialized")

    def _ensure_started(self):
        """Ensure scheduler is started"""
        if not self._started:
            try:
                self.scheduler.start()
                self._started = True
                logger.info("Scheduler started")
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
    
    async def create_schedule(self, request: ScheduleCreateRequest) -> VideoSchedule:
        """Create a new video schedule"""
        try:
            self._ensure_started()
            # Get video asset information
            video_asset = video_service.get_video_asset(request.video_id)
            if not video_asset:
                raise ValueError(f"Video asset {request.video_id} not found")
            
            # Generate schedule ID
            schedule_id = str(uuid.uuid4())
            
            # Create video URL
            video_url = f"http://localhost:8080/api/v1/videos/{request.video_id}/player"
            
            # Calculate next send time
            next_send = self._calculate_next_send(request.scheduled_date, request.frequency, request.custom_cron)
            
            # Create schedule object
            schedule = VideoSchedule(
                id=schedule_id,
                video_id=request.video_id,
                video_title=video_asset.filename,
                video_url=video_url,
                recipient_email=request.recipient_email,
                recipient_name=request.recipient_name,
                sender_name=request.sender_name,
                scheduled_date=request.scheduled_date,
                frequency=request.frequency,
                custom_cron=request.custom_cron,
                timezone=request.timezone,
                subject=request.subject,
                message=request.message,
                template=request.template,
                include_thumbnail=request.include_thumbnail,
                include_duration=request.include_duration,
                auto_expire=request.auto_expire,
                next_send=next_send
            )
            
            # Store schedule
            self.schedules[schedule_id] = schedule
            
            # Add job to scheduler
            await self._add_scheduler_job(schedule)
            
            logger.info(f"Created schedule {schedule_id} for video {request.video_id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {str(e)}")
            raise
    
    async def update_schedule(self, schedule_id: str, request: ScheduleUpdateRequest) -> VideoSchedule:
        """Update an existing schedule"""
        if schedule_id not in self.schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        schedule = self.schedules[schedule_id]
        
        # Update fields
        if request.recipient_email:
            schedule.recipient_email = request.recipient_email
        if request.recipient_name is not None:
            schedule.recipient_name = request.recipient_name
        if request.sender_name:
            schedule.sender_name = request.sender_name
        if request.scheduled_date:
            schedule.scheduled_date = request.scheduled_date
        if request.frequency:
            schedule.frequency = request.frequency
        if request.custom_cron is not None:
            schedule.custom_cron = request.custom_cron
        if request.timezone:
            schedule.timezone = request.timezone
        if request.subject:
            schedule.subject = request.subject
        if request.message is not None:
            schedule.message = request.message
        if request.template:
            schedule.template = request.template
        if request.status:
            schedule.status = request.status
        if request.include_thumbnail is not None:
            schedule.include_thumbnail = request.include_thumbnail
        if request.include_duration is not None:
            schedule.include_duration = request.include_duration
        if request.auto_expire is not None:
            schedule.auto_expire = request.auto_expire
        
        schedule.updated_at = datetime.now()
        
        # Recalculate next send time
        schedule.next_send = self._calculate_next_send(
            schedule.scheduled_date, schedule.frequency, schedule.custom_cron
        )
        
        # Remove old job and add new one
        self.scheduler.remove_job(schedule_id, jobstore=None)
        await self._add_scheduler_job(schedule)
        
        logger.info(f"Updated schedule {schedule_id}")
        return schedule
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        if schedule_id not in self.schedules:
            return False
        
        # Remove from scheduler
        try:
            self.scheduler.remove_job(schedule_id)
        except:
            pass  # Job might not exist
        
        # Remove from storage
        del self.schedules[schedule_id]
        
        logger.info(f"Deleted schedule {schedule_id}")
        return True
    
    def get_schedule(self, schedule_id: str) -> Optional[VideoSchedule]:
        """Get a schedule by ID"""
        return self.schedules.get(schedule_id)
    
    def list_schedules(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """List all schedules with pagination"""
        schedules = list(self.schedules.values())
        total = len(schedules)
        
        # Simple pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_schedules = schedules[start:end]
        
        return {
            "schedules": paginated_schedules,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    
    def get_calendar_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Get calendar events for a date range"""
        events = []
        
        for schedule in self.schedules.values():
            if schedule.status == ScheduleStatus.ACTIVE:
                # Generate events based on frequency
                event_dates = self._generate_event_dates(schedule, start_date, end_date)
                
                for event_date in event_dates:
                    events.append(CalendarEvent(
                        id=f"{schedule.id}_{event_date.isoformat()}",
                        title=f"📧 {schedule.video_title}",
                        start=event_date,
                        description=f"Send video to {schedule.recipient_email}",
                        video_id=schedule.video_id,
                        recipient_email=schedule.recipient_email,
                        status=schedule.status,
                        frequency=schedule.frequency
                    ))
        
        return sorted(events, key=lambda x: x.start)
    
    async def _add_scheduler_job(self, schedule: VideoSchedule):
        """Add a job to the APScheduler"""
        if schedule.status != ScheduleStatus.ACTIVE:
            return
        
        # Create timezone object
        tz = pytz.timezone(schedule.timezone)
        
        # Create trigger based on frequency
        if schedule.frequency == FrequencyType.ONCE:
            trigger = DateTrigger(run_date=schedule.scheduled_date, timezone=tz)
        elif schedule.frequency == FrequencyType.DAILY:
            trigger = CronTrigger(
                hour=schedule.scheduled_date.hour,
                minute=schedule.scheduled_date.minute,
                timezone=tz
            )
        elif schedule.frequency == FrequencyType.WEEKLY:
            trigger = CronTrigger(
                day_of_week=schedule.scheduled_date.weekday(),
                hour=schedule.scheduled_date.hour,
                minute=schedule.scheduled_date.minute,
                timezone=tz
            )
        elif schedule.frequency == FrequencyType.MONTHLY:
            trigger = CronTrigger(
                day=schedule.scheduled_date.day,
                hour=schedule.scheduled_date.hour,
                minute=schedule.scheduled_date.minute,
                timezone=tz
            )
        elif schedule.frequency == FrequencyType.CUSTOM and schedule.custom_cron:
            # Parse custom cron expression
            cron_parts = schedule.custom_cron.split()
            if len(cron_parts) == 5:
                trigger = CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4],
                    timezone=tz
                )
            else:
                logger.error(f"Invalid cron expression: {schedule.custom_cron}")
                return
        else:
            logger.error(f"Unsupported frequency: {schedule.frequency}")
            return
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self._send_scheduled_email,
            trigger=trigger,
            id=schedule.id,
            args=[schedule.id],
            replace_existing=True
        )
        
        logger.info(f"Added scheduler job for schedule {schedule.id}")
    
    async def _send_scheduled_email(self, schedule_id: str):
        """Send scheduled email"""
        try:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                logger.error(f"Schedule {schedule_id} not found")
                return
            
            # Check if schedule is still active
            if schedule.status != ScheduleStatus.ACTIVE:
                logger.info(f"Schedule {schedule_id} is not active, skipping")
                return
            
            # Check auto-expire
            if schedule.auto_expire and datetime.now() > schedule.auto_expire:
                schedule.status = ScheduleStatus.COMPLETED
                logger.info(f"Schedule {schedule_id} auto-expired")
                return
            
            # Get video asset
            video_asset = video_service.get_video_asset(schedule.video_id)
            if not video_asset:
                logger.error(f"Video asset {schedule.video_id} not found")
                return
            
            # Send email
            result = await email_service.send_video_email(schedule, video_asset)
            
            # Update schedule
            schedule.last_sent = datetime.now()
            schedule.send_count += 1
            
            if result["success"]:
                logger.info(f"Successfully sent email for schedule {schedule_id}")
                
                # If it's a one-time schedule, mark as completed
                if schedule.frequency == FrequencyType.ONCE:
                    schedule.status = ScheduleStatus.COMPLETED
                    self.scheduler.remove_job(schedule_id)
            else:
                logger.error(f"Failed to send email for schedule {schedule_id}: {result.get('error_message')}")
                
        except Exception as e:
            logger.error(f"Error sending scheduled email {schedule_id}: {str(e)}")
    
    def _calculate_next_send(self, scheduled_date: datetime, frequency: FrequencyType, custom_cron: Optional[str]) -> datetime:
        """Calculate next send time based on frequency"""
        now = datetime.now()
        
        if frequency == FrequencyType.ONCE:
            return scheduled_date if scheduled_date > now else now
        elif frequency == FrequencyType.DAILY:
            next_send = scheduled_date
            while next_send <= now:
                next_send += timedelta(days=1)
            return next_send
        elif frequency == FrequencyType.WEEKLY:
            next_send = scheduled_date
            while next_send <= now:
                next_send += timedelta(weeks=1)
            return next_send
        elif frequency == FrequencyType.MONTHLY:
            next_send = scheduled_date
            while next_send <= now:
                # Add one month (approximate)
                if next_send.month == 12:
                    next_send = next_send.replace(year=next_send.year + 1, month=1)
                else:
                    next_send = next_send.replace(month=next_send.month + 1)
            return next_send
        else:
            return scheduled_date
    
    def _generate_event_dates(self, schedule: VideoSchedule, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate event dates for calendar view"""
        events = []
        current_date = max(schedule.scheduled_date, start_date)
        
        if schedule.frequency == FrequencyType.ONCE:
            if start_date <= schedule.scheduled_date <= end_date:
                events.append(schedule.scheduled_date)
        elif schedule.frequency == FrequencyType.DAILY:
            while current_date <= end_date:
                if current_date >= start_date:
                    events.append(current_date)
                current_date += timedelta(days=1)
        elif schedule.frequency == FrequencyType.WEEKLY:
            while current_date <= end_date:
                if current_date >= start_date:
                    events.append(current_date)
                current_date += timedelta(weeks=1)
        elif schedule.frequency == FrequencyType.MONTHLY:
            while current_date <= end_date:
                if current_date >= start_date:
                    events.append(current_date)
                # Add one month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        return events


# Global service instance
scheduler_service = SchedulerService()
