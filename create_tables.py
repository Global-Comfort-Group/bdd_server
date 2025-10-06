"""
Script to create all database tables for BDD Property Tracker
"""
import asyncio
from app.core.database import async_engine, Base

async def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Import models to register them with Base.metadata
    from app.models.user import User
    from app.models.enums import UserRole, PropertyType, PropertyStatus
    from app.models.property import Property, PropertyAttachment  
    from app.models.workflow import WorkflowHistory
    
    try:
        async with async_engine.begin() as conn:
            # Drop all tables first (for clean slate)
            print("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("Dropped existing tables")
            
            # Create all tables
            print("Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("Created all tables")
        
        print("✅ Database tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_tables())