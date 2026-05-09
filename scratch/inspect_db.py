import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    print(f"Connecting to {mongo_url}...")
    client = AsyncIOMotorClient(mongo_url)
    try:
        dbs = await client.list_database_names()
        print(f"Databases: {dbs}")
        for db_name in ['AutoNorth', 'autonorth']:
            if db_name in dbs or True: # Check even if not in list_database_names (sometimes they don't show up if empty or permissions)
                db = client[db_name]
                colls = await db.list_collection_names()
                print(f"\nDB: {db_name}")
                print(f"Collections: {colls}")
                for c in colls:
                    count = await db[c].count_documents({})
                    print(f"  - {c}: {count} documents")
                    if c == 'users':
                        users = await db[c].find({}).to_list(10)
                        for u in users:
                            print(f"    - User: {u.get('email')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
