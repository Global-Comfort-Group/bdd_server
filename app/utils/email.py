import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import resend

from app.core.config import settings


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def _send_email_sync(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """Send email synchronously."""
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            print("Email configuration not complete. Email not sent.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add plain text part
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """Send email asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._send_email_sync, 
            to_emails, 
            subject, 
            body, 
            html_body
        )
    
    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        subject = f"Welcome to {settings.PROJECT_NAME}"
        body = f"""
        Hello {user_name},
        
        Welcome to {settings.PROJECT_NAME}! Your account has been created successfully.
        
        You can now log in and start managing properties.
        
        Best regards,
        The {settings.PROJECT_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to {settings.PROJECT_NAME}!</h2>
            <p>Hello {user_name},</p>
            <p>Welcome to {settings.PROJECT_NAME}! Your account has been created successfully.</p>
            <p>You can now log in and start managing properties.</p>
            <br>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return await self.send_email([user_email], subject, body, html_body)
    
    async def send_password_reset_email(
        self, user_email: str, user_name: str, reset_token: str
    ) -> bool:
        """Send password reset email."""
        subject = f"{settings.PROJECT_NAME} - Password Reset"
        # In a real application, you'd have a frontend URL here
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        
        body = f"""
        Hello {user_name},
        
        You requested a password reset for your {settings.PROJECT_NAME} account.
        
        Please click the following link to reset your password:
        {reset_url}
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The {settings.PROJECT_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user_name},</p>
            <p>You requested a password reset for your {settings.PROJECT_NAME} account.</p>
            <p><a href="{reset_url}">Click here to reset your password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return await self.send_email([user_email], subject, body, html_body)
    async def send_property_created_notification(
        self,
        property_data: Dict[str, Any],
        submitter_data: Dict[str, Any]
    ) -> bool:
        """Send email notification when a property is created using Resend."""
        if not settings.RESEND_API_KEY or not settings.NOTIFICATION_EMAIL:
            print("Resend email configuration not complete. Email not sent.")
            return False

        try:
            # Configure Resend
            resend.api_key = settings.RESEND_API_KEY

            # Format prices
            formatted_price = f"₱{property_data.get('price', 0):,.2f}" if property_data.get('price') else 'N/A'
            formatted_lease_price = f"₱{property_data.get('lease_price', 0):,.2f}" if property_data.get('lease_price') else 'N/A'

            # Create HTML email
            html_body = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <style>
                  body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                  .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                  .header {{ background-color: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                  .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                  .property-details {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                  .detail-row {{ margin: 10px 0; }}
                  .label {{ font-weight: bold; color: #4F46E5; }}
                  .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1 style="margin: 0;">🏢 New Property Added</h1>
                  </div>
                  <div class="content">
                    <p>A new property has been submitted to the BDD Property Tracker.</p>

                    <div class="property-details">
                      <div class="detail-row">
                        <span class="label">Property Name:</span> {property_data.get('name', 'N/A')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Property ID:</span> #{property_data.get('id', 'N/A')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Address:</span> {property_data.get('address', 'N/A')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Property Type:</span> {property_data.get('propertyType', 'N/A')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Transaction Status:</span> {property_data.get('transactionStatus', 'N/A')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Sale Price:</span> {formatted_price}
                      </div>
                      <div class="detail-row">
                        <span class="label">Lease Price:</span> {formatted_lease_price}
                      </div>
                      <div class="detail-row">
                        <span class="label">Submitted By:</span> {submitter_data.get('firstName', '')} {submitter_data.get('lastName', '')}
                      </div>
                      <div class="detail-row">
                        <span class="label">Submitter Email:</span> {submitter_data.get('email', 'N/A')}
                      </div>
                      {f'<div class="detail-row"><span class="label">Company:</span> {submitter_data.get("company")}</div>' if submitter_data.get('company') else ''}
                      <div class="detail-row">
                        <span class="label">Date Submitted:</span> {property_data.get('createdAt', 'N/A')}
                      </div>
                    </div>

                    <p style="margin-top: 20px;">
                      <a href="https://bdd-client-staging.up.railway.app/property/{property_data.get('id', '')}"
                         style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Property Details
                      </a>
                    </p>
                  </div>
                  <div class="footer">
                    <p>This is an automated notification from BDD Property Tracker</p>
                  </div>
                </div>
              </body>
            </html>
            """

            # Send email via Resend
            params = {
                "from": "BDD Property Tracker <onboarding@resend.dev>",
                "to": [settings.NOTIFICATION_EMAIL],
                "subject": f"New Property Added: {property_data.get('name', 'Unknown')}",
                "html": html_body
            }

            email_result = resend.Emails.send(params)
            print(f"✅ Property creation email sent via Resend: {email_result}")
            return True

        except Exception as e:
            print(f"❌ Failed to send property creation email via Resend: {e}")
            return False
