"""
Email service for sending verification emails and notifications
Supports Alibaba DirectMail and SendGrid
"""
import os
from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        """Initialize email service based on provider"""
        self.provider = os.getenv("EMAIL_PROVIDER", "alibaba")  # or "sendgrid"
        
        if self.provider == "alibaba":
            self._init_alibaba()
        elif self.provider == "sendgrid":
            self._init_sendgrid()
    
    def _init_alibaba(self):
        """Initialize Alibaba DirectMail"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkdm.request.v20151123 import SingleSendMailRequest
            
            self.access_key = os.getenv("ALIBABA_ACCESS_KEY_ID")
            self.access_secret = os.getenv("ALIBABA_ACCESS_KEY_SECRET")
            self.region = os.getenv("ALIBABA_REGION", "ap-southeast-1")
            self.from_email = os.getenv("EMAIL_FROM_ADDRESS", "noreply@yourdomain.com")
            
            self.client = AcsClient(self.access_key, self.access_secret, self.region)
            logger.info("✅ Alibaba DirectMail initialized")
        except Exception as e:
            logger.warning(f"⚠️  Alibaba DirectMail not configured: {e}")
            self.client = None
    
    def _init_sendgrid(self):
        """Initialize SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            
            self.api_key = os.getenv("SENDGRID_API_KEY")
            self.from_email = os.getenv("EMAIL_FROM_ADDRESS", "noreply@yourdomain.com")
            
            self.client = SendGridAPIClient(self.api_key)
            logger.info("✅ SendGrid initialized")
        except Exception as e:
            logger.warning(f"⚠️  SendGrid not configured: {e}")
            self.client = None
    
    async def send_verification_email(
        self, 
        to_email: str, 
        verification_code: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send verification email with code"""
        
        subject = "Verify Your BDD Property Tracker Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9fafb; }}
                .code-box {{ 
                    background: white; 
                    border: 2px solid #3b82f6; 
                    padding: 20px; 
                    text-align: center; 
                    font-size: 32px; 
                    font-weight: bold;
                    letter-spacing: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BDD Property Tracker</h1>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Hi {user_name or 'there'},</p>
                    <p>Thank you for registering with BDD Property Tracker. Please use the verification code below to complete your registration:</p>
                    
                    <div class="code-box">
                        {verification_code}
                    </div>
                    
                    <p>This code will expire in 15 minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 BDD Property Tracker. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email"""
        
        reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - BDD Property Tracker"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9fafb; }}
                .button {{ 
                    display: inline-block;
                    background: #3b82f6;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BDD Property Tracker</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>Hi {user_name or 'there'},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <a href="{reset_link}" class="button">Reset Password</a>
                    
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>© 2025 BDD Property Tracker. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email via configured provider"""
        
        if not self.client:
            logger.warning("⚠️  Email service not configured - skipping email send")
            # In development, just log instead of sending
            if os.getenv("ENVIRONMENT") == "development":
                logger.info(f"📧 Would send email to {to_email}: {subject}")
                return True
            return False
        
        try:
            if self.provider == "alibaba":
                return await self._send_via_alibaba(to_email, subject, html_content)
            elif self.provider == "sendgrid":
                return await self._send_via_sendgrid(to_email, subject, html_content)
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    async def _send_via_alibaba(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send via Alibaba DirectMail"""
        from aliyunsdkdm.request.v20151123 import SingleSendMailRequest
        
        request = SingleSendMailRequest.SingleSendMailRequest()
        request.set_AccountName(self.from_email)
        request.set_AddressType(1)
        request.set_ReplyToAddress("false")
        request.set_ToAddress(to_email)
        request.set_Subject(subject)
        request.set_HtmlBody(html_content)
        
        response = self.client.do_action_with_exception(request)
        logger.info(f"✅ Email sent to {to_email}")
        return True
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send via SendGrid"""
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        response = self.client.send(message)
        logger.info(f"✅ Email sent to {to_email} (status: {response.status_code})")
        return True


# Global instance
email_service = EmailService()


