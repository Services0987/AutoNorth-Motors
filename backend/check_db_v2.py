import asyncio
import os
import sys

# Add current dir to path to import local_db
sys.path.append(os.getcwd())

async def check():
    try:
        from local_db import get_db
        db = await get_db()
        
        # Check sessions
        sessions = await db.sessions.find({}).to_list(20)
        print(f"Sessions ({len(sessions)}):")
        for s in sessions:
            print(f"  - {s.get('_id')} (Created: {s.get('created_at')})")
            
        # Check settings
        general = await db.settings.find_one({'type': 'general'})
        print(f"General Settings: {general}")
        
        scraper = await db.settings.find_one({'type': 'scraper'})
        print(f"Scraper Settings: {scraper}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
