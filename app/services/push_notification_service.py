"""
Push notification service for mobile/browser notifications
Add to existing monolith - no separate service needed!
"""
import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications"""
    
    def __init__(self):
        """Initialize push notification provider"""
        self.provider = os.getenv("PUSH_PROVIDER", "firebase")  # or "onesignal"
        
        if self.provider == "firebase":
            self._init_firebase()
        elif self.provider == "onesignal":
            self._init_onesignal()
    
    def _init_firebase(self):
        """Initialize Firebase Cloud Messaging (FCM)"""
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path and not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.messaging = messaging
            logger.info("✅ Firebase Cloud Messaging initialized")
        except Exception as e:
            logger.warning(f"⚠️  Firebase not configured: {e}")
            self.messaging = None
    
    def _init_onesignal(self):
        """Initialize OneSignal"""
        try:
            self.app_id = os.getenv("ONESIGNAL_APP_ID")
            self.api_key = os.getenv("ONESIGNAL_API_KEY")
            logger.info("✅ OneSignal initialized")
        except Exception as e:
            logger.warning(f"⚠️  OneSignal not configured: {e}")
    
    async def send_push_notification(
        self,
        user_token: str,  # Device token from frontend
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send push notification to a device"""
        
        if not self.messaging and self.provider == "firebase":
            logger.warning("⚠️  Push notifications not configured")
            return False
        
        try:
            if self.provider == "firebase":
                return await self._send_via_firebase(user_token, title, body, data)
            elif self.provider == "onesignal":
                return await self._send_via_onesignal(user_token, title, body, data)
        except Exception as e:
            logger.error(f"❌ Failed to send push notification: {e}")
            return False
    
    async def _send_via_firebase(
        self,
        user_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send via Firebase Cloud Messaging"""
        
        message = self.messaging.Message(
            notification=self.messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user_token,
        )
        
        response = self.messaging.send(message)
        logger.info(f"✅ Push notification sent: {response}")
        return True
    
    async def _send_via_onesignal(
        self,
        user_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send via OneSignal"""
        import httpx
        
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "app_id": self.app_id,
            "include_player_ids": [user_token],
            "headings": {"en": title},
            "contents": {"en": body},
            "data": data or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://onesignal.com/api/v1/notifications",
                headers=headers,
                json=payload
            )
        
        logger.info(f"✅ Push notification sent via OneSignal")
        return response.status_code == 200
    
    async def send_to_multiple_devices(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> int:
        """Send push notification to multiple devices"""
        success_count = 0
        
        for token in tokens:
            if await self.send_push_notification(token, title, body, data):
                success_count += 1
        
        return success_count


# Global instance
push_service = PushNotificationService()

