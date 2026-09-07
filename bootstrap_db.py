"""Bootstrap a fresh database (new environment only).

The Alembic chain starts from a schema that predates it: revision cb38ae4a1822
already references the `user` table, so `alembic upgrade head` cannot build an
empty database from scratch. For a brand-new environment the correct sequence
is to create every table from the models, then stamp the chain as applied so
that future migrations run normally.

Refuses to run against a database that already has tables — use `alembic
upgrade head` there instead.

    python bootstrap_db.py
"""
import asyncio
import sys

from sqlalchemy import inspect

from alembic import command
from alembic.config import Config

from app.core.database import async_engine, Base

# Importing the package registers every mapped model on Base.metadata.
import app.models  # noqa: F401
from app.models import draft_nego_table, verification  # noqa: F401


async def create_schema() -> bool:
    async with async_engine.begin() as conn:
        existing = await conn.run_sync(lambda c: inspect(c).get_table_names())
        if existing:
            print(f"❌ Database already has {len(existing)} table(s); refusing to bootstrap.")
            print("   Run `alembic upgrade head` instead.")
            return False

        print(f"Creating {len(Base.metadata.tables)} tables from models...")
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Schema created:")
    for name in sorted(Base.metadata.tables):
        print(f"  - {name}")
    return True


def stamp_head() -> None:
    print("Stamping Alembic at head...")
    command.stamp(Config("alembic.ini"), "head")
    print("✅ Alembic stamped at head")


async def main() -> int:
    if not await create_schema():
        return 1
    stamp_head()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
