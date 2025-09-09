"""
Script to create sample users for each role in BDD Property Tracker
Run this script to populate the database with test users
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import get_password_hash

async def create_sample_users():
    """Create sample users for testing and development"""
    
    async with AsyncSessionLocal() as db:
        # Check if users already exist
        existing_users = await db.execute(select(User.email))
        existing_emails = {row[0] for row in existing_users.fetchall()}
        
        sample_users = [
            # Admin Portal Users (Separate Portal)
            {
                "email": "admin@bdd.com",
                "password": "admin123",
                "first_name": "System",
                "last_name": "Administrator",
                "role": UserRole.ADMIN,
                "company": "BDD Property Tracker",
                "phone": "+63917000001"
            },
            
            # Main Property Management Portal Users
            {
                "email": "bdd.user@bdd.com",
                "password": "bdduser123",
                "first_name": "BDD",
                "last_name": "User",
                "role": UserRole.BDD_USER,
                "company": "BDD Property Tracker",
                "phone": "+63917000002"
            },
            {
                "email": "agent@realty.com",
                "password": "agent123",
                "first_name": "Property",
                "last_name": "Agent",
                "role": UserRole.AGENT,
                "company": "Premium Realty Co.",
                "phone": "+63917000003"
            },
            {
                "email": "broker@brokers.com",
                "password": "broker123",
                "first_name": "Senior",
                "last_name": "Broker",
                "role": UserRole.BROKER,
                "company": "Elite Property Brokers",
                "phone": "+63917000004"
            }
        ]
        
        created_users = []
        
        for user_data in sample_users:
            if user_data["email"] not in existing_emails:
                # Hash the password
                hashed_password = get_password_hash(user_data["password"])
                
                # Create user object
                user = User(
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    company=user_data["company"],
                    phone=user_data["phone"],
                    is_active=True,
                    is_verified=True,
                    is_superuser=(user_data["role"] == UserRole.ADMIN)
                )
                
                db.add(user)
                created_users.append(user_data)
                print(f"✅ Created user: {user_data['email']} ({user_data['role'].value})")
            else:
                print(f"⚠️  User already exists: {user_data['email']}")
        
        await db.commit()
        
        if created_users:
            print(f"\n🎉 Successfully created {len(created_users)} sample users!")
            print("\n📝 Login Credentials:")
            print("=" * 50)
            
            # Admin Portal
            print("\n🔧 ADMIN PORTAL (Separate Portal):")
            admin_users = [u for u in sample_users if u["role"] == UserRole.ADMIN]
            for user in admin_users:
                print(f"  Email: {user['email']}")
                print(f"  Password: {user['password']}")
                print(f"  Role: {user['role'].value}")
                print(f"  Purpose: System administration, user management")
                print()
            
            # Property Management Portal
            print("🏢 PROPERTY MANAGEMENT PORTAL:")
            property_users = [u for u in sample_users if u["role"] != UserRole.ADMIN]
            for user in property_users:
                print(f"  Email: {user['email']}")
                print(f"  Password: {user['password']}")
                print(f"  Role: {user['role'].value}")
                if user["role"] == UserRole.BDD_USER:
                    print(f"  Purpose: Full property access, internal BDD operations")
                elif user["role"] == UserRole.AGENT:
                    print(f"  Purpose: Submit properties, track submissions")
                elif user["role"] == UserRole.BROKER:
                    print(f"  Purpose: Review properties, approve/reject submissions")
                print()
                
        else:
            print("ℹ️  All sample users already exist in the database.")

if __name__ == "__main__":
    asyncio.run(create_sample_users())