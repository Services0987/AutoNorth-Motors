import asyncio
import os
import sys
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

async def verify_api():
    try:
        from local_db import get_db
        db = await get_db('autonorth')
        
        # 1. Check Public Vehicles
        query = {
            "status": {"$in": [None, "available", "Available", "AVAILABLE"]},
            "show_on_home": {"$ne": False}
        }
        v_count = await db.vehicles.count_documents(query)
        print(f"Publicly Visible Vehicles: {v_count}")
        
        # 2. Check Settings
        settings = await db.settings.find_one({"type": "general"})
        print(f"AI Provider: {settings.get('ai_provider') if settings else 'NONE'}")
        
        # 3. Check Leads
        l_count = await db.leads.count_documents({})
        print(f"Leads in DB: {l_count}")
        
        if v_count == 0:
            print("WARNING: No vehicles are publicly visible!")
        else:
            print("SUCCESS: Vehicles are visible.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_api())
