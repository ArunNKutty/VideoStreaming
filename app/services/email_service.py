"""
Email service using Resend for sending video notifications
"""
import os
import resend
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.models.scheduler import VideoSchedule, EmailTemplate
from app.models.video import VideoAsset
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY", "your-resend-api-key")


class EmailService:
    """Service for sending emails via Resend"""
    
    def __init__(self):
        self.from_email = os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
        self.base_url = f"http://localhost:{settings.PORT}"
    
    async def send_video_email(self, schedule: VideoSchedule, video_asset: VideoAsset) -> Dict[str, Any]:
        """Send video email using the specified template"""
        try:
            # Generate email content based on template
            email_content = self._generate_email_content(schedule, video_asset)
            
            # Send email via Resend
            response = resend.Emails.send({
                "from": f"{schedule.sender_name} <{self.from_email}>",
                "to": [schedule.recipient_email],
                "subject": schedule.subject,
                "html": email_content["html"],
                "text": email_content["text"]
            })
            
            logger.info(f"Email sent successfully to {schedule.recipient_email}, ID: {response.get('id')}")
            
            return {
                "success": True,
                "message_id": response.get("id"),
                "sent_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {schedule.recipient_email}: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "sent_at": datetime.now()
            }
    
    def _generate_email_content(self, schedule: VideoSchedule, video_asset: VideoAsset) -> Dict[str, str]:
        """Generate email content based on template"""
        
        # Common variables
        video_url = f"{self.base_url}/api/v1/videos/{schedule.video_id}/player"
        thumbnail_url = f"{self.base_url}/api/v1/videos/{schedule.video_id}/thumbnail" if schedule.include_thumbnail else None
        
        context = {
            "recipient_name": schedule.recipient_name or "Valued Viewer",
            "sender_name": schedule.sender_name,
            "video_title": schedule.video_title,
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "custom_message": schedule.message,
            "duration": video_asset.info.duration if video_asset.info and schedule.include_duration else None,
            "current_year": datetime.now().year
        }
        
        if schedule.template == EmailTemplate.STANDARD:
            return self._standard_template(context)
        elif schedule.template == EmailTemplate.PREMIUM:
            return self._premium_template(context)
        elif schedule.template == EmailTemplate.MINIMAL:
            return self._minimal_template(context)
        else:
            return self._standard_template(context)
    
    def _standard_template(self, ctx: Dict[str, Any]) -> Dict[str, str]:
        """Standard email template"""
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Video is Ready!</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 12px;
                    padding: 40px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                .video-card {{
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    overflow: hidden;
                    margin: 30px 0;
                }}
                .video-thumbnail {{
                    width: 100%;
                    height: 200px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 48px;
                }}
                .video-info {{
                    padding: 20px;
                }}
                .video-title {{
                    font-size: 20px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: #2c3e50;
                }}
                .video-meta {{
                    color: #6c757d;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .watch-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-weight: 600;
                    text-align: center;
                    transition: transform 0.2s;
                }}
                .watch-button:hover {{
                    transform: translateY(-2px);
                }}
                .message {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎬 {ctx['sender_name']}</div>
                    <h1>Your Video is Ready to Watch!</h1>
                    <p>Hi {ctx['recipient_name']}, we're excited to share this video with you.</p>
                </div>
                
                <div class="video-card">
                    <div class="video-thumbnail">
                        🎥
                    </div>
                    <div class="video-info">
                        <div class="video-title">{ctx['video_title']}</div>
                        {f'<div class="video-meta">Duration: {int(ctx["duration"]//60)}:{int(ctx["duration"]%60):02d}</div>' if ctx['duration'] else ''}
                        <a href="{ctx['video_url']}" class="watch-button">▶️ Watch Now</a>
                    </div>
                </div>
                
                {f'<div class="message">{ctx["custom_message"]}</div>' if ctx['custom_message'] else ''}
                
                <div class="footer">
                    <p>This video was shared with you by {ctx['sender_name']}</p>
                    <p>© {ctx['current_year']} Video Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Your Video is Ready!
        
        Hi {ctx['recipient_name']},
        
        We're excited to share this video with you: {ctx['video_title']}
        
        {f"Duration: {int(ctx['duration']//60)}:{int(ctx['duration']%60):02d}" if ctx['duration'] else ''}
        
        Watch now: {ctx['video_url']}
        
        {ctx['custom_message'] if ctx['custom_message'] else ''}
        
        Best regards,
        {ctx['sender_name']}
        """
        
        return {"html": html, "text": text}
    
    def _premium_template(self, ctx: Dict[str, Any]) -> Dict[str, str]:
        """Premium email template with enhanced design"""
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Exclusive Video Content</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    max-width: 650px;
                    margin: 0 auto;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .email-wrapper {{
                    padding: 40px 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px;
                }}
                .video-showcase {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .video-preview {{
                    position: relative;
                    background: #000;
                    border-radius: 12px;
                    overflow: hidden;
                    margin-bottom: 20px;
                    height: 250px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                }}
                .play-icon {{
                    width: 80px;
                    height: 80px;
                    background: rgba(255,255,255,0.9);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 30px;
                    color: #667eea;
                    cursor: pointer;
                    transition: transform 0.3s;
                }}
                .play-icon:hover {{
                    transform: scale(1.1);
                }}
                .video-title {{
                    font-size: 24px;
                    font-weight: 600;
                    margin: 20px 0 10px 0;
                    color: #2c3e50;
                }}
                .video-description {{
                    color: #7f8c8d;
                    margin-bottom: 30px;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    padding: 16px 40px;
                    border-radius: 50px;
                    font-weight: 600;
                    font-size: 16px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    transition: all 0.3s;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                }}
                .cta-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                }}
                .features {{
                    display: flex;
                    justify-content: space-around;
                    margin: 40px 0;
                    text-align: center;
                }}
                .feature {{
                    flex: 1;
                    padding: 0 10px;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                .feature-text {{
                    font-size: 14px;
                    color: #7f8c8d;
                }}
                .message-box {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 25px;
                    border-radius: 12px;
                    margin: 30px 0;
                    border-left: 4px solid #667eea;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="container">
                    <div class="header">
                        <h1>🎬 Exclusive Content</h1>
                        <p>Premium video experience delivered to {ctx['recipient_name']}</p>
                    </div>
                    
                    <div class="content">
                        <div class="video-showcase">
                            <div class="video-preview">
                                <div class="play-icon">▶️</div>
                            </div>
                            <div class="video-title">{ctx['video_title']}</div>
                            <div class="video-description">
                                {f"Runtime: {int(ctx['duration']//60)}:{int(ctx['duration']%60):02d}" if ctx['duration'] else 'High-quality video content'}
                            </div>
                            <a href="{ctx['video_url']}" class="cta-button">Watch Now</a>
                        </div>
                        
                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">🎥</div>
                                <div class="feature-text">HD Quality</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">📱</div>
                                <div class="feature-text">Mobile Friendly</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">⚡</div>
                                <div class="feature-text">Fast Streaming</div>
                            </div>
                        </div>
                        
                        {f'<div class="message-box">{ctx["custom_message"]}</div>' if ctx['custom_message'] else ''}
                    </div>
                    
                    <div class="footer">
                        <p>Delivered by {ctx['sender_name']} • © {ctx['current_year']} Video Platform</p>
                        <p>Experience the future of video sharing</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        🎬 EXCLUSIVE CONTENT
        
        Hi {ctx['recipient_name']},
        
        You have exclusive access to: {ctx['video_title']}
        
        {f"Runtime: {int(ctx['duration']//60)}:{int(ctx['duration']%60):02d}" if ctx['duration'] else ''}
        
        ▶️ Watch Now: {ctx['video_url']}
        
        Features:
        • HD Quality streaming
        • Mobile-friendly player
        • Fast loading
        
        {ctx['custom_message'] if ctx['custom_message'] else ''}
        
        Delivered by {ctx['sender_name']}
        """
        
        return {"html": html, "text": text}
    
    def _minimal_template(self, ctx: Dict[str, Any]) -> Dict[str, str]:
        """Minimal email template"""
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Video Link</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 500px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    background-color: #ffffff;
                }}
                .content {{
                    text-align: center;
                }}
                .video-title {{
                    font-size: 22px;
                    font-weight: 600;
                    margin: 20px 0;
                    color: #2c3e50;
                }}
                .watch-link {{
                    display: inline-block;
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 600;
                    padding: 12px 24px;
                    border: 2px solid #667eea;
                    border-radius: 6px;
                    margin: 20px 0;
                    transition: all 0.2s;
                }}
                .watch-link:hover {{
                    background: #667eea;
                    color: white;
                }}
                .message {{
                    margin: 30px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 6px;
                }}
                .footer {{
                    margin-top: 40px;
                    font-size: 14px;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="content">
                <p>Hi {ctx['recipient_name']},</p>
                
                <div class="video-title">{ctx['video_title']}</div>
                
                {f'<div>Duration: {int(ctx["duration"]//60)}:{int(ctx["duration"]%60):02d}</div>' if ctx['duration'] else ''}
                
                <a href="{ctx['video_url']}" class="watch-link">Watch Video</a>
                
                {f'<div class="message">{ctx["custom_message"]}</div>' if ctx['custom_message'] else ''}
                
                <div class="footer">
                    <p>Sent by {ctx['sender_name']}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Hi {ctx['recipient_name']},
        
        {ctx['video_title']}
        {f"Duration: {int(ctx['duration']//60)}:{int(ctx['duration']%60):02d}" if ctx['duration'] else ''}
        
        Watch: {ctx['video_url']}
        
        {ctx['custom_message'] if ctx['custom_message'] else ''}
        
        - {ctx['sender_name']}
        """
        
        return {"html": html, "text": text}


# Global service instance
email_service = EmailService()
