import asyncio
import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

async def seed():
    try:
        from local_db import get_db
        db = await get_db('autonorth')
        
        # Seed Settings
        await db.settings.update_one(
            {'type': 'general'},
            {'$set': {
                'ai_provider': 'local',
                'ai_api_key': '',
                'ai_model': 'gemini-1.5-flash',
                'ai_health': 'online',
                'ai_error': '',
                'updated_at': datetime.now(timezone.utc)
            }},
            upsert=True
        )
        print("Settings seeded.")
        
        # Ensure vehicles have status 'available' and 'show_on_home' = True
        result = await db.vehicles.update_many(
            {},
            {'$set': {'status': 'available', 'show_on_home': True}}
        )
        print(f"Updated {result.modified_count} vehicles to 'available'.")
        
        # Wait for the persistence loop to flush to disk
        print("Waiting for disk flush...")
        await asyncio.sleep(2)
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
