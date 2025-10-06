"""
Fix password hashes for existing users
This script re-hashes all user passwords to ensure compatibility
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

# Passwords for sample users (same as create_sample_users.py)
USER_PASSWORDS = {
    "admin@bdd.com": "admin123",
    "bdd.user@bdd.com": "bdduser123",
    "agent@realty.com": "agent123",
    "broker@brokers.com": "broker123"
}

async def fix_passwords():
    """Re-hash passwords for all users"""
    
    async with AsyncSessionLocal() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("⚠️  No users found in database")
            return
        
        print(f"Found {len(users)} users")
        print("")
        
        # Update each user's password
        updated_count = 0
        for user in users:
            if user.email in USER_PASSWORDS:
                # Re-hash the password
                new_password = USER_PASSWORDS[user.email]
                user.hashed_password = get_password_hash(new_password)
                updated_count += 1
                print(f"✅ Fixed password hash for: {user.email}")
            else:
                print(f"⚠️  Unknown user (skipping): {user.email}")
        
        await db.commit()
        
        print("")
        if updated_count > 0:
            print(f"🎉 Successfully fixed {updated_count} user passwords!")
            print("Users can now log in with their original passwords.")
        else:
            print("ℹ️  No passwords were updated.")

if __name__ == "__main__":
    asyncio.run(fix_passwords())

