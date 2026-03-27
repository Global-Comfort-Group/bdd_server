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
    @staticmethod
    def _format_property_type(raw: str) -> str:
        return {
            'LAND_ONLY': 'Land Only',
            'LAND_AND_BUILDING': 'Land & Building',
            'BUILDING_ONLY': 'Building Only',
        }.get(raw, raw)

    @staticmethod
    def _format_transaction_status(raw: str) -> str:
        return {
            'S': 'For Sale',
            'L': 'For Lease',
            'SL': 'Sale & Lease',
            'JV': 'Joint Venture',
        }.get(raw, raw)

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
            price_val = property_data.get('price')
            lease_price_val = property_data.get('lease_price')
            formatted_price = f"&#8369;{float(price_val):,.2f}" if price_val else None
            formatted_lease_price = f"&#8369;{float(lease_price_val):,.2f}" if lease_price_val else None

            # Format date
            created_at = property_data.get('createdAt', '')
            try:
                formatted_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%B %d, %Y') if created_at else 'N/A'
            except Exception:
                formatted_date = created_at or 'N/A'

            property_id = property_data.get('id', '')
            property_name = property_data.get('name', 'N/A')
            property_url = f"{settings.FRONTEND_URL}/property/{property_id}"
            submitter_name = f"{submitter_data.get('firstName', '')} {submitter_data.get('lastName', '')}".strip() or 'N/A'
            submitter_email = submitter_data.get('email', 'N/A')
            company = submitter_data.get('company', '') or '—'
            property_type = self._format_property_type(property_data.get('propertyType', ''))
            transaction = self._format_transaction_status(property_data.get('transactionStatus', ''))
            address = property_data.get('address', 'N/A')

            raw_txn = property_data.get('transactionStatus', '')

            # Pre-compute price stat card (3rd column of the dark stats bar)
            if raw_txn in ('S', 'SL') and formatted_price:
                price_stat_td = formatted_price
            elif raw_txn in ('L', 'SL') and formatted_lease_price:
                price_stat_td = formatted_lease_price + ' / mo'
            elif raw_txn == 'JV' and formatted_price:
                price_stat_td = formatted_price
            else:
                price_stat_td = 'TBD'

            # Pre-compute green pricing section (body area)
            pricing_rows = ''
            if raw_txn in ('S', 'SL') and formatted_price:
                pricing_rows += (
                    '<tr><td style="font-size:13px;font-weight:600;color:#16a34a;padding-bottom:4px">Sale Price</td>'
                    '<td align="right" style="font-size:20px;font-weight:900;color:#15803d;padding-bottom:4px">' + formatted_price + '</td></tr>'
                )
            if raw_txn in ('L', 'SL') and formatted_lease_price:
                pricing_rows += (
                    '<tr><td style="font-size:13px;font-weight:600;color:#16a34a;padding-top:8px">Lease Price / mo</td>'
                    '<td align="right" style="font-size:20px;font-weight:900;color:#15803d;padding-top:8px">' + formatted_lease_price + '</td></tr>'
                )
            if raw_txn == 'JV' and formatted_price:
                pricing_rows += (
                    '<tr><td style="font-size:13px;font-weight:600;color:#16a34a">Price</td>'
                    '<td align="right" style="font-size:20px;font-weight:900;color:#15803d">' + formatted_price + '</td></tr>'
                )

            if pricing_rows:
                pricing_section = (
                    '<p style="margin:28px 0 16px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em">Pricing</p>'
                    '<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #dcfce7;border-radius:12px;overflow:hidden;background:#f0fdf4">'
                    '<tr><td style="padding:20px 24px">'
                    '<table width="100%" cellpadding="0" cellspacing="0">' + pricing_rows + '</table>'
                    '</td></tr></table>'
                )
            else:
                pricing_section = ''

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
</head>
<body style="margin:0;padding:0;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">

<table width="100%" cellpadding="0" cellspacing="0">

  <!-- ── HEADER ── -->
  <tr>
    <td style="background:linear-gradient(135deg,#A31520 0%,#CC1F2C 60%,#E8374A 100%);padding:36px 48px 32px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:rgba(255,255,255,.18);border-radius:10px;width:44px;height:44px;text-align:center;vertical-align:middle;font-size:22px;font-weight:900;color:#fff">B</td>
                <td style="padding-left:12px;font-size:17px;font-weight:800;color:#fff;vertical-align:middle">GCGC BDD Tracker</td>
              </tr>
            </table>
          </td>
          <td align="right" style="vertical-align:top">
            <span style="background:rgba(255,255,255,.18);border-radius:20px;padding:5px 14px;font-size:12px;font-weight:700;color:rgba(255,220,220,0.9)">#{property_id}</span>
          </td>
        </tr>
      </table>
      <h1 style="margin:28px 0 8px;font-size:30px;font-weight:900;color:#fff;letter-spacing:-.5px;line-height:1.15">New Property Submission</h1>
      <p style="margin:0 0 24px;font-size:15px;color:rgba(255,220,220,0.85);line-height:1.6">A new property has been submitted to GCGC BDD Property Tracker and is awaiting review.</p>
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="background:rgba(255,255,255,.18);border-radius:20px;padding:5px 16px;font-size:12px;font-weight:700;color:#fff">{property_type}</td>
          <td width="8"></td>
          <td style="background:rgba(255,255,255,.18);border-radius:20px;padding:5px 16px;font-size:12px;font-weight:700;color:#fff">{transaction}</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── STATS BAR ── -->
  <tr>
    <td style="background:#f8fafc;border-bottom:1px solid #e2e8f0;padding:20px 48px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:33%;padding-right:12px">
            <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em">Property Type</p>
            <p style="margin:0;font-size:15px;font-weight:700;color:#1e293b">{property_type}</p>
          </td>
          <td style="width:33%;border-left:1px solid #e2e8f0;padding:0 12px">
            <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em">Transaction</p>
            <p style="margin:0;font-size:15px;font-weight:700;color:#CC1F2C">{transaction}</p>
          </td>
          <td style="width:33%;border-left:1px solid #e2e8f0;padding-left:12px">
            <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em">Price</p>
            <p style="margin:0;font-size:15px;font-weight:700;color:#16a34a">{price_stat_td}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── BODY ── -->
  <tr>
    <td style="background:#ffffff;padding:36px 48px">

      <!-- Property Details -->
      <p style="margin:0 0 14px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em">Property Details</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:28px">
        <tr style="background:#f8fafc">
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;width:36%;border-bottom:1px solid #e2e8f0">Property Name</td>
          <td style="padding:13px 18px;font-size:14px;font-weight:700;color:#0f172a;border-bottom:1px solid #e2e8f0">{property_name}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;border-bottom:1px solid #e2e8f0">Address</td>
          <td style="padding:13px 18px;font-size:14px;color:#334155;border-bottom:1px solid #e2e8f0">{address}</td>
        </tr>
        <tr style="background:#f8fafc">
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;border-bottom:1px solid #e2e8f0">Property Type</td>
          <td style="padding:13px 18px;font-size:14px;color:#334155;border-bottom:1px solid #e2e8f0">{property_type}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500">Transaction</td>
          <td style="padding:13px 18px"><span style="background:#FFF5F5;color:#CC1F2C;font-size:12px;font-weight:700;padding:3px 12px;border-radius:20px;border:1px solid #FECACA">{transaction}</span></td>
        </tr>
      </table>

      <!-- Pricing -->
      {pricing_section}

      <!-- Submitted By -->
      <p style="margin:0 0 14px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em">Submitted By</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:32px">
        <tr style="background:#f8fafc">
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;width:36%;border-bottom:1px solid #e2e8f0">Name</td>
          <td style="padding:13px 18px;font-size:14px;font-weight:700;color:#0f172a;border-bottom:1px solid #e2e8f0">{submitter_name}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;border-bottom:1px solid #e2e8f0">Email</td>
          <td style="padding:13px 18px;border-bottom:1px solid #e2e8f0"><a href="mailto:{submitter_email}" style="color:#CC1F2C;font-size:14px;font-weight:600;text-decoration:none">{submitter_email}</a></td>
        </tr>
        <tr style="background:#f8fafc">
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500;border-bottom:1px solid #e2e8f0">Company</td>
          <td style="padding:13px 18px;font-size:14px;color:#334155;border-bottom:1px solid #e2e8f0">{company}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;font-size:13px;color:#64748b;font-weight:500">Date Submitted</td>
          <td style="padding:13px 18px;font-size:14px;color:#334155">{formatted_date}</td>
        </tr>
      </table>

      <!-- CTA -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td align="center">
            <a href="{property_url}" style="display:inline-block;background:linear-gradient(135deg,#A31520,#CC1F2C,#E8374A);color:#fff;text-decoration:none;font-size:15px;font-weight:700;padding:16px 52px;border-radius:10px;letter-spacing:-.2px;box-shadow:0 4px 15px rgba(204,31,44,0.4)">View Property &rarr;</a>
          </td>
        </tr>
      </table>

    </td>
  </tr>

  <!-- ── FOOTER ── -->
  <tr>
    <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:24px 48px;text-align:center">
      <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#64748b">GCGC BDD Property Tracker</p>
      <p style="margin:0;font-size:12px;color:#94a3b8">Automated notification &nbsp;&middot;&nbsp; Do not reply &nbsp;&middot;&nbsp; &copy; 2026 GCGC BDD Property Tracker</p>
    </td>
  </tr>

</table>

</body>
</html>"""

            params = {
                "from": "BDD Property Tracker <noreply@hotelsogo-ai.com>",
                "to": [settings.NOTIFICATION_EMAIL],
                "subject": f"[New Submission] {property_name} — {transaction}",
                "html": html,
            }

            email_result = resend.Emails.send(params)
            print(f"✅ Property creation email sent via Resend: {email_result}")
            return True

        except Exception as e:
            print(f"❌ Failed to send property creation email via Resend: {e}")
            return False
