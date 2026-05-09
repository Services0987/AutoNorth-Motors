import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

async def check():
    try:
        from local_db import get_db
        # Check both names
        for name in ['autonorth', 'AutoNorth']:
            db = await get_db(name)
            v_count = await db.vehicles.count_documents({})
            s = await db.settings.find_one({'type': 'general'})
            print(f"DB: {name} -> Vehicles: {v_count}, Settings: {bool(s)}")
            # If one is empty and other is not, we have a sync issue
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
