"""
Quick script to approve all existing users in the database
Run this to fix the 401 login error
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.enums import AccountStatus

async def approve_all_users():
    """Set all users to APPROVED status so they can log in"""
    
    async with AsyncSessionLocal() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("⚠️  No users found in database")
            return
        
        print(f"Found {len(users)} users")
        print("")
        
        # Update each user to APPROVED
        updated_count = 0
        for user in users:
            if user.account_status != AccountStatus.APPROVED:
                user.account_status = AccountStatus.APPROVED
                updated_count += 1
                print(f"✅ Approved: {user.email} (was: {user.account_status.value if hasattr(user.account_status, 'value') else 'PENDING'})")
            else:
                print(f"✓  Already approved: {user.email}")
        
        await db.commit()
        
        print("")
        if updated_count > 0:
            print(f"🎉 Successfully approved {updated_count} users!")
            print("Users can now log in.")
        else:
            print("ℹ️  All users were already approved.")

if __name__ == "__main__":
    asyncio.run(approve_all_users())

