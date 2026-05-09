import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    uri = os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URL") or "mongodb://localhost:27017"
    db_name = os.environ.get("DB_NAME", "autonorth")
    print(f"Connecting to {uri}, DB: {db_name}")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    try:
        v_count = await db.vehicles.count_documents({})
        print(f"Vehicles: {v_count}")
        
        if v_count > 0:
            sample = await db.vehicles.find_one({})
            print(f"Sample: {sample.get('title')}")
            
        dbs = await client.list_database_names()
        print(f"All DBs: {dbs}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
