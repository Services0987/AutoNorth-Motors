"""
Lightweight async MongoDB-compatible storage layer with JSON persistence.

Wraps mongomock-motor for an in-memory MongoDB-like API and persists every
mutation to a JSON file on disk so data survives restarts. This lets the
existing FastAPI/Motor code keep working without a real MongoDB server.
"""
import asyncio
import json
import os
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient
from motor.motor_asyncio import AsyncIOMotorClient


DATA_DIR = pathlib.Path(os.environ.get("LOCAL_DB_DIR", "backend/.data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "autonorth_db.json"


def _json_default(o: Any) -> Any:
    if isinstance(o, ObjectId):
        return {"$oid": str(o)}
    if isinstance(o, datetime):
        return {"$date": o.isoformat()}
    raise TypeError(f"Cannot serialize {type(o).__name__}")


def _json_object_hook(d: Dict[str, Any]) -> Any:
    if set(d.keys()) == {"$oid"}:
        return ObjectId(d["$oid"])
    if set(d.keys()) == {"$date"}:
        try:
            return datetime.fromisoformat(d["$date"])
        except Exception:
            return datetime.now(timezone.utc)
    return d


class PersistentDatabase:
    """Wraps an AsyncMongoMockClient database and persists writes to disk."""

    def __init__(self, db_name: str = "AutoNorth"):
        uri = os.environ.get("MONGODB_URI")
        if uri:
            print(f"[local_db] Connecting to real MongoDB...")
            self._client = AsyncIOMotorClient(uri)
            self._is_mock = False
        else:
            print(f"[local_db] Using in-memory mock MongoDB (data will be lost on Vercel restart)...")
            self._client = AsyncMongoMockClient()
            self._is_mock = True

        self._db = self._client[db_name]
        self._db_name = db_name
        self._lock = asyncio.Lock()
        self._save_task: asyncio.Task | None = None
        self._dirty = False

    async def load_from_disk(self) -> None:
        if not self._is_mock or not DATA_FILE.exists():
            return
        try:
            raw = DATA_FILE.read_text(encoding="utf-8")
            if not raw.strip():
                return
            data = json.loads(raw, object_hook=_json_object_hook)
        except Exception as exc:  # pragma: no cover - corrupt file
            print(f"[local_db] Failed to load {DATA_FILE}: {exc}")
            return
        for coll_name, docs in data.items():
            if not docs:
                continue
            await self._db[coll_name].insert_many(docs)

    async def _dump_to_disk(self) -> None:
        snapshot: Dict[str, List[Dict[str, Any]]] = {}
        for coll_name in await self._db.list_collection_names():
            cursor = self._db[coll_name].find({})
            docs = await cursor.to_list(length=None)
            snapshot[coll_name] = docs
        tmp = DATA_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(snapshot, default=_json_default), encoding="utf-8")
        tmp.replace(DATA_FILE)

    def schedule_save(self) -> None:
        """Coalesce many writes into a single disk flush (only for mock)."""
        if not self._is_mock:
            return
        self._dirty = True
        if self._save_task and not self._save_task.done():
            return
        loop = asyncio.get_event_loop()
        self._save_task = loop.create_task(self._save_loop())

    async def _save_loop(self) -> None:
        try:
            await asyncio.sleep(0.4)
            async with self._lock:
                if self._dirty:
                    self._dirty = False
                    await self._dump_to_disk()
        except Exception as exc:  # pragma: no cover
            print(f"[local_db] Save error: {exc}")

    def __getattr__(self, name: str) -> Any:
        # Forward unknown attributes to the underlying mongomock-motor db,
        # wrapping collection access so writes trigger disk persistence.
        if name.startswith("_"):
            raise AttributeError(name)
        attr = getattr(self._db, name)
        if hasattr(attr, "insert_one"):  # it's a Collection
            return _PersistedCollection(attr, self)
        return attr

    def __getitem__(self, name: str) -> Any:
        coll = self._db[name]
        return _PersistedCollection(coll, self)

    async def list_collection_names(self) -> List[str]:
        return await self._db.list_collection_names()


class _PersistedCollection:
    """Proxy around a mongomock-motor collection that schedules saves on writes."""

    _WRITE_OPS = {
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one", "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace", "find_one_and_delete",
        "bulk_write",
    }

    def __init__(self, coll: Any, parent: PersistentDatabase):
        self._coll = coll
        self._parent = parent

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._coll, name)
        if name in self._WRITE_OPS and callable(attr):
            parent = self._parent

            async def wrapped(*args, **kwargs):
                result = await attr(*args, **kwargs)
                parent.schedule_save()
                return result

            return wrapped
        return attr


_DB: PersistentDatabase | None = None


async def get_db(db_name: str = "AutoNorth") -> PersistentDatabase:
    global _DB
    if _DB is None:
        _DB = PersistentDatabase(db_name)
        await _DB.load_from_disk()
    return _DB
