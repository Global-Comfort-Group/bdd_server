"""
Debug script to check table metadata
"""
from app.core.database import Base
from app.models.user import User
from app.models.property import Property, PropertyAttachment
from app.models.workflow import WorkflowHistory

print("Registered tables in Base.metadata:")
for table_name, table in Base.metadata.tables.items():
    print(f"  {table_name}: {table}")

print(f"\nUser table name: {User.__tablename__}")
print(f"User table: {User.__table__}")

print(f"\nProperty table name: {Property.__tablename__}")

# Check foreign key references
for table_name, table in Base.metadata.tables.items():
    print(f"\nTable: {table_name}")
    for column in table.columns:
        if column.foreign_keys:
            for fk in column.foreign_keys:
                print(f"  Column {column.name} -> {fk}")