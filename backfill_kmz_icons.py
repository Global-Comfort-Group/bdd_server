"""
Backfill icon data into already-uploaded KMZ files.

KMZ uploads store a cached GeoJSON FeatureCollection (``parsed_data``). Older
rows were parsed before the parser learned to resolve each placemark's icon
(the Google Earth icon URL + scale + anchor). This script re-downloads each
KMZ from OSS, re-parses it with the current parser, and updates ``parsed_data``
and ``feature_count`` in place.

NON-DESTRUCTIVE: only rewrites the parsed cache; never touches the original
archive in OSS. Safe to re-run (idempotent).

Run once after deploying the icon-aware parser:
    python backfill_kmz_icons.py
"""
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
import app.models  # noqa: F401  (populate Base.metadata / relationships)
from app.models.property_kmz import PropertyKMZ
from app.services.kmz_parser import KMZParseError, parse_kmz
from app.services.oss_service import get_oss_service


async def backfill() -> None:
    oss = get_oss_service()
    updated = skipped = failed = 0

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(PropertyKMZ))).scalars().all()
        print(f"Found {len(rows)} KMZ record(s) to re-parse.")

        for kmz in rows:
            try:
                data = oss.download_file_content(kmz.oss_object_key)
                geojson = parse_kmz(data)
            except (KMZParseError, Exception) as exc:  # noqa: BLE001
                failed += 1
                print(f"  ✗ id={kmz.id} {kmz.filename!r}: {type(exc).__name__}: {exc}")
                continue

            icon_count = sum(
                1 for f in geojson.get("features", [])
                if (f.get("properties") or {}).get("icon")
            )
            kmz.parsed_data = geojson
            kmz.feature_count = len(geojson.get("features", []))
            updated += 1
            print(
                f"  ✓ id={kmz.id} {kmz.filename!r}: "
                f"{kmz.feature_count} features, {icon_count} with icons"
            )

        await session.commit()

    print(f"\nDone. updated={updated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    asyncio.run(backfill())
