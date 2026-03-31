"""
SMS service for sending verification codes and notifications
Supports Alibaba SMS and Twilio
"""
import os
import random
from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages"""
    
    def __init__(self):
        """Initialize SMS service based on provider"""
        self.provider = os.getenv("SMS_PROVIDER", "alibaba")  # or "twilio"
        
        if self.provider == "alibaba":
            self._init_alibaba()
        elif self.provider == "twilio":
            self._init_twilio()
    
    def _init_alibaba(self):
        """Initialize Alibaba SMS Service"""
        try:
            from aliyunsdkcore.client import AcsClient
            
            self.access_key = os.getenv("ALIBABA_ACCESS_KEY_ID")
            self.access_secret = os.getenv("ALIBABA_ACCESS_KEY_SECRET")
            self.region = os.getenv("ALIBABA_REGION", "ap-southeast-1")
            self.sign_name = os.getenv("ALIBABA_SMS_SIGN_NAME", "BDD Property")
            
            # Template codes (you need to create these in Alibaba SMS console)
            self.verification_template = os.getenv("ALIBABA_SMS_VERIFICATION_TEMPLATE", "SMS_123456789")
            
            self.client = AcsClient(self.access_key, self.access_secret, self.region)
            logger.info("✅ Alibaba SMS Service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Alibaba SMS not configured: {e}")
            self.client = None
    
    def _init_twilio(self):
        """Initialize Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.from_phone = os.getenv("TWILIO_PHONE_NUMBER")
            
            self.client = Client(account_sid, auth_token)
            logger.info("✅ Twilio initialized")
        except Exception as e:
            logger.warning(f"⚠️  Twilio not configured: {e}")
            self.client = None
    
    def generate_verification_code(self, length: int = 6) -> str:
        """Generate random verification code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    async def send_verification_sms(
        self,
        phone_number: str,
        verification_code: str
    ) -> bool:
        """Send SMS verification code"""
        
        message = f"Your BDD Property Tracker verification code is: {verification_code}. Valid for 15 minutes."
        
        return await self.send_sms(phone_number, message, verification_code)
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        verification_code: Optional[str] = None
    ) -> bool:
        """Send SMS via configured provider"""
        
        if not self.client:
            logger.warning("⚠️  SMS service not configured - skipping SMS send")
            # In development, just log instead of sending
            if os.getenv("ENVIRONMENT") == "development":
                logger.info(f"📱 Would send SMS to {phone_number}: {message}")
                return True
            return False
        
        try:
            if self.provider == "alibaba":
                return await self._send_via_alibaba(phone_number, verification_code)
            elif self.provider == "twilio":
                return await self._send_via_twilio(phone_number, message)
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")
            raise HTTPException(status_code=500, detail="Failed to send SMS")
    
    async def _send_via_alibaba(self, phone_number: str, verification_code: str) -> bool:
        """Send via Alibaba SMS"""
        from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
        import json
        
        request = SendSmsRequest.SendSmsRequest()
        request.set_PhoneNumbers(phone_number)
        request.set_SignName(self.sign_name)
        request.set_TemplateCode(self.verification_template)
        request.set_TemplateParam(json.dumps({"code": verification_code}))
        
        response = self.client.do_action_with_exception(request)
        logger.info(f"✅ SMS sent to {phone_number}")
        return True
    
    async def _send_via_twilio(self, phone_number: str, message: str) -> bool:
        """Send via Twilio"""
        
        message = self.client.messages.create(
            body=message,
            from_=self.from_phone,
            to=phone_number
        )
        
        logger.info(f"✅ SMS sent to {phone_number} (SID: {message.sid})")
        return True


# Global instance
sms_service = SMSService()

