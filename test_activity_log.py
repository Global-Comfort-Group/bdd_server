"""
Quick test script to create a test activity log entry
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.activity_log import ActivityLog, ActivityAction, ResourceType
from datetime import datetime


async def create_test_log():
    async with AsyncSessionLocal() as db:
        # Create a test log entry
        test_log = ActivityLog(
            user_id=1,  # Admin user
            action=ActivityAction.LOGIN,
            resource_type=ResourceType.SYSTEM,
            details="Test login activity - manual entry",
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            created_at=datetime.utcnow()
        )
        
        db.add(test_log)
        await db.commit()
        await db.refresh(test_log)
        
        print(f"✅ Created test activity log:")
        print(f"   ID: {test_log.id}")
        print(f"   User ID: {test_log.user_id}")
        print(f"   Action: {test_log.action}")
        print(f"   Details: {test_log.details}")
        print(f"\n🎉 Now check your Activity Logs page in the admin panel!")


if __name__ == "__main__":
    asyncio.run(create_test_log())





