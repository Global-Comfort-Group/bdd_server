"""
Safely create the `property_kmz_files` table in the current database.

NON-DESTRUCTIVE: uses Base.metadata.create_all(checkfirst=True) scoped to a single
table. It only issues CREATE TABLE if the table is missing and never drops or alters
existing tables/data. Use this instead of `alembic upgrade head` (the migration chain
is currently broken) and instead of `create_tables.py` (which DROPS all tables).

Run once after deploying the KMZ feature:
    python create_kmz_table.py
"""
import asyncio

from app.core.database import async_engine, Base
# Import all models so Base.metadata is fully populated and FKs resolve.
import app.models  # noqa: F401
from app.models.property_kmz import PropertyKMZ


async def create_kmz_table() -> None:
    table = PropertyKMZ.__table__
    print(f"Ensuring table '{table.name}' exists (non-destructive)...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[table], checkfirst=True)
    print(f"✅ Table '{table.name}' is present (created if it was missing).")


if __name__ == "__main__":
    asyncio.run(create_kmz_table())
