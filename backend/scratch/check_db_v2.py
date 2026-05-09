import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    uri = os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URL") or "mongodb://localhost:27017"
    print(f"Connecting to: {uri[:20]}...")
    client = AsyncIOMotorClient(uri)
    
    try:
        dbs = await client.list_database_names()
        print(f"Databases: {dbs}")
        
        for db_name in ["AutoNorth", "autonorth"]:
            if db_name in dbs:
                db = client[db_name]
                cols = await db.list_collection_names()
                print(f"Collections in {db_name}: {cols}")
                if "users" in cols:
                    users = await db.users.count_documents({})
                    print(f"Users in {db_name}: {users}")
                if "vehicles" in cols:
                    vehicles = await db.vehicles.count_documents({})
                    print(f"Vehicles in {db_name}: {vehicles}")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
