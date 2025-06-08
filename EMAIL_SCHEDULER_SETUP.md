# 📧 Video Email Scheduler Setup Guide

## 🎯 Overview

The Video Email Scheduler allows you to schedule beautiful email notifications for your video content using Resend email service. Features include:

- **Multiple Email Templates**: Standard, Premium, and Minimal designs
- **Flexible Scheduling**: Once, Daily, Weekly, Monthly, or Custom frequencies
- **Calendar Interface**: Visual scheduling with FullCalendar.js
- **React Components**: Modern UI for schedule management
- **Automated Delivery**: Background job processing with APScheduler

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Backend dependencies
pip install resend apscheduler python-crontab

# Frontend dependencies (already included)
# FullCalendar.js is loaded via CDN
```

### 2. Configure Resend Email Service

1. **Sign up for Resend**: Go to [resend.com](https://resend.com) and create an account
2. **Get API Key**: Generate an API key from your Resend dashboard
3. **Verify Domain**: Add and verify your sending domain in Resend

### 3. Environment Configuration

Create a `.env` file with your email settings:

```env
# Email Configuration (Resend)
RESEND_API_KEY=re_your_resend_api_key_here
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Video Platform
```

### 4. Start the Services

```bash
# Start backend server
python main.py

# Start React frontend (in another terminal)
cd react-hls-player
npm start
```

## 📧 Email Templates

### Standard Template
- Clean, professional design
- Video thumbnail placeholder
- Duration information
- Call-to-action button
- Responsive layout

### Premium Template
- Luxury gradient design
- Enhanced visual elements
- Feature highlights
- Premium branding
- Advanced styling

### Minimal Template
- Simple, clean layout
- Essential information only
- Lightweight design
- Fast loading

## 📅 Using the Scheduler

### Web Interface

1. **Access the Scheduler**:
   - React App: http://localhost:3000 → "Email Scheduler" tab
   - Calendar View: http://localhost:8080/api/v1/calendar

2. **Create a Schedule**:
   - Click "New Schedule"
   - Enter video ID (from your video assets)
   - Set recipient email and name
   - Choose date, time, and frequency
   - Select email template
   - Add custom message (optional)
   - Submit the form

3. **Manage Schedules**:
   - View all schedules in the dashboard
   - See statistics (total, active, emails sent)
   - Delete schedules as needed

### API Usage

```bash
# Create a new schedule
curl -X POST "http://localhost:8080/api/v1/schedules" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "a0692aec-f0f2-4922-86b0-cac1790548b6",
    "recipient_email": "user@example.com",
    "recipient_name": "John Doe",
    "scheduled_date": "2024-12-25T10:00:00",
    "frequency": "once",
    "subject": "Your Christmas Video is Ready!",
    "template": "premium",
    "message": "Merry Christmas! Enjoy this special video."
  }'

# List all schedules
curl "http://localhost:8080/api/v1/schedules"

# Get calendar events
curl "http://localhost:8080/api/v1/calendar/events"
```

## 🔧 Configuration Options

### Frequency Types

- **once**: Send email once at the specified time
- **daily**: Send daily at the specified time
- **weekly**: Send weekly on the same day and time
- **monthly**: Send monthly on the same date and time
- **custom**: Use custom cron expression

### Email Template Options

```python
# Template selection
{
  "template": "standard",    # Professional design
  "template": "premium",     # Luxury design
  "template": "minimal"      # Simple design
}
```

### Schedule Options

```python
{
  "include_thumbnail": true,     # Include video thumbnail
  "include_duration": true,      # Show video duration
  "auto_expire": "2024-12-31T23:59:59",  # Auto-expire date
  "timezone": "UTC"              # Timezone for scheduling
}
```

## 🎨 Customizing Email Templates

### Modify Existing Templates

Edit the templates in `app/services/email_service.py`:

```python
def _standard_template(self, ctx: Dict[str, Any]) -> Dict[str, str]:
    # Customize HTML and text content
    html = f"""
    <!-- Your custom HTML template -->
    """
    text = f"""
    Your custom text template
    """
    return {"html": html, "text": text}
```

### Add New Templates

1. Add new template type to `EmailTemplate` enum in `app/models/scheduler.py`
2. Create template method in `EmailService`
3. Update template selection in frontend

## 📊 Monitoring and Analytics

### Schedule Statistics

- **Total Schedules**: Number of created schedules
- **Active Schedules**: Currently running schedules
- **Emails Sent**: Total emails delivered
- **Completed**: Finished schedules

### Calendar View

- Visual representation of scheduled emails
- Monthly, weekly, and daily views
- Event details on click
- Real-time updates

## 🔍 Troubleshooting

### Common Issues

1. **Emails Not Sending**:
   - Check Resend API key
   - Verify domain authentication
   - Check server logs for errors

2. **Schedule Not Created**:
   - Verify video ID exists
   - Check date format (ISO 8601)
   - Validate email address format

3. **Calendar Not Loading**:
   - Check browser console for errors
   - Verify API endpoints are accessible
   - Check CORS configuration

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### API Testing

Use the interactive API docs at http://localhost:8080/docs to test endpoints.

## 🚀 Production Deployment

### Environment Variables

```env
# Production settings
DEBUG=false
LOG_LEVEL=WARNING
RESEND_API_KEY=your_production_api_key
FROM_EMAIL=noreply@yourdomain.com

# Database (recommended for production)
DATABASE_URL=postgresql://user:pass@localhost:5432/videoplatform

# Redis for job queues
REDIS_URL=redis://localhost:6379/0
```

### Database Setup

For production, replace in-memory storage with a database:

1. Set up PostgreSQL
2. Run database migrations
3. Update scheduler service to use database

### Scaling Considerations

- Use Redis for job queues
- Deploy multiple worker processes
- Set up monitoring and alerting
- Configure email rate limiting

## 📚 API Reference

### Endpoints

- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/schedules` - List schedules
- `GET /api/v1/schedules/{id}` - Get schedule
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule
- `GET /api/v1/calendar` - Calendar interface
- `GET /api/v1/calendar/events` - Calendar events

### Models

See `app/models/scheduler.py` for complete data models and validation rules.

## 🎉 Success!

Your video email scheduler is now ready to send beautiful, automated email notifications for your video content!

For support or questions, check the API documentation at `/docs` or review the source code in the repository.
