import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import resend
from datetime import datetime

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
            resend.api_key = settings.RESEND_API_KEY

            # Format prices
            formatted_price = f"₱{property_data.get('price', 0):,.2f}" if property_data.get('price') else 'N/A'
            formatted_lease_price = f"₱{property_data.get('lease_price', 0):,.2f}" if property_data.get('lease_price') else 'N/A'

            # Format date
            created_at = property_data.get('createdAt', '')
            try:
                formatted_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%B %d, %Y') if created_at else 'N/A'
            except Exception:
                formatted_date = created_at or 'N/A'

            property_id = property_data.get('id', '')
            property_url = f"{settings.FRONTEND_URL}/property/{property_id}"

            template_id = getattr(settings, 'RESEND_TEMPLATE_ID', None)

            if template_id:
                # Use Resend template with variables (flat dict — Resend format)
                params = {
                    "from": "BDD Property Tracker <noreply@hotelsogo-ai.com>",
                    "to": [settings.NOTIFICATION_EMAIL],
                    "subject": f"New Property Submission: {property_data.get('name', 'Unknown')}",
                    "template_id": template_id,
                    "variables": {
                        "property_name":      property_data.get('name', 'N/A'),
                        "property_id":        str(property_id),
                        "address":            property_data.get('address', 'N/A'),
                        "property_type":      property_data.get('propertyType', 'N/A'),
                        "transaction_status": property_data.get('transactionStatus', 'N/A'),
                        "sale_price":         formatted_price,
                        "lease_price":        formatted_lease_price,
                        "submitter_name":     f"{submitter_data.get('firstName', '')} {submitter_data.get('lastName', '')}".strip(),
                        "submitter_email":    submitter_data.get('email', 'N/A'),
                        "company":            submitter_data.get('company', ''),
                        "submitted_date":     formatted_date,
                        "property_url":       property_url,
                    }
                }
            else:
                # Fallback: plain inline HTML (no template configured)
                params = {
                    "from": "BDD Property Tracker <noreply@hotelsogo-ai.com>",
                    "to": [settings.NOTIFICATION_EMAIL],
                    "subject": f"New Property Submission: {property_data.get('name', 'Unknown')}",
                    "html": f"""
                    <p><strong>New property submitted to BDD Property Tracker.</strong></p>
                    <ul>
                      <li><strong>Name:</strong> {property_data.get('name', 'N/A')}</li>
                      <li><strong>ID:</strong> #{property_id}</li>
                      <li><strong>Address:</strong> {property_data.get('address', 'N/A')}</li>
                      <li><strong>Type:</strong> {property_data.get('propertyType', 'N/A')}</li>
                      <li><strong>Transaction:</strong> {property_data.get('transactionStatus', 'N/A')}</li>
                      <li><strong>Sale Price:</strong> {formatted_price}</li>
                      <li><strong>Lease Price:</strong> {formatted_lease_price}</li>
                      <li><strong>Submitted By:</strong> {submitter_data.get('firstName', '')} {submitter_data.get('lastName', '')} ({submitter_data.get('email', 'N/A')})</li>
                      <li><strong>Date:</strong> {formatted_date}</li>
                    </ul>
                    <p><a href="{property_url}">View Property</a></p>
                    """
                }

            email_result = resend.Emails.send(params)
            print(f"✅ Property creation email sent via Resend: {email_result}")
            return True

        except Exception as e:
            print(f"❌ Failed to send property creation email via Resend: {e}")
            return False
