import asyncio
import os
import sys

# Add current dir to path to import local_db
sys.path.append(os.getcwd())

async def check():
    try:
        from local_db import get_db
        db = await get_db()
        # Try 'general' type (repo_clone style)
        s = await db.settings.find_one({'type': 'general'})
        print(f"General Settings: {s}")
        # Try 'scraper' type (AUTONORTH style?)
        s2 = await db.settings.find_one({'_id': 'scraper'})
        print(f"Scraper Settings: {s2}")
        # List all collections
        colls = await db.list_collection_names()
        print(f"Collections: {colls}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
