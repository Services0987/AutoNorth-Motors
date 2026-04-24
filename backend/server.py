"""AutoNorth Motors API - FastAPI backend with persistent local storage."""
from dotenv import load_dotenv
load_dotenv()

import os
import re
import io
import csv
import jwt
import bcrypt
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, Dict

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from pydantic import BaseModel, Field

from local_db import get_db, PersistentDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = os.environ.get("DB_NAME", "AutoNorth")
JWT_ALGORITHM = "HS256"
db: Optional[PersistentDatabase] = None

app = FastAPI(title="AutoNorth Motors API")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # cookies use SameSite=Lax with same-origin proxy instead
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# ─── Auth helpers ─────────────────────────────────────────────────
def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def jwt_secret() -> str:
    return os.environ.get("JWT_SECRET", "autonorth-dev-secret-please-change")


def create_token(user_id: str, email: str, exp_hours: int = 24) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=exp_hours),
        },
        jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def to_object_id(value: Any) -> Optional[ObjectId]:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return None


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    oid = to_object_id(payload.get("sub"))
    if not oid:
        raise HTTPException(401, "Invalid token subject")
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(401, "User not found")
    user["_id"] = str(user["_id"])
    return user


# ─── Models ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class VehicleCreate(BaseModel):
    title: str
    make: Optional[str] = ""
    model: Optional[str] = ""
    year: Optional[int] = 2024
    price: Optional[float] = 0
    mileage: Optional[int] = 0
    condition: Optional[str] = "used"
    body_type: Optional[str] = "Sedan"
    fuel_type: Optional[str] = "Gas"
    transmission: Optional[str] = "Automatic"
    exterior_color: Optional[str] = ""
    interior_color: Optional[str] = ""
    engine: Optional[str] = ""
    drivetrain: Optional[str] = ""
    doors: Optional[int] = 4
    seats: Optional[int] = 5
    vin: Optional[str] = ""
    stock_number: Optional[str] = ""
    description: Optional[str] = ""
    features: List[str] = []
    images: List[str] = []
    status: str = "available"
    featured: bool = False
    show_on_home: bool = False


class VehicleUpdate(BaseModel):
    title: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    condition: Optional[str] = None
    body_type: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    engine: Optional[str] = None
    drivetrain: Optional[str] = None
    vin: Optional[str] = None
    stock_number: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    status: Optional[str] = None
    featured: Optional[bool] = None
    show_on_home: Optional[bool] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    lead_type: Optional[str] = "contact"
    message: Optional[str] = ""
    vehicle_id: Optional[str] = None
    source: Optional[str] = "website"


class LeadStatusUpdate(BaseModel):
    status: str


class BulkImageImport(BaseModel):
    urls: List[str]


class BulkDeleteRequest(BaseModel):
    vehicle_ids: List[str]


class ScraperImportRequest(BaseModel):
    url: str  # allow newline-separated URLs


# ─── Public endpoints ─────────────────────────────────────────────
@api_router.get("/health")
async def health():
    total = await db.vehicles.count_documents({})
    return {"status": "ok", "vehicles": total}


@api_router.post("/auth/login")
async def login(data: LoginRequest, response: Response):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    uid = str(user["_id"])
    token = create_token(uid, email)
    # Same-origin cookie via the FastAPI proxy (HTTP-only).
    response.set_cookie(
        "access_token", token,
        httponly=True, secure=False, samesite="lax",
        max_age=86400, path="/",
    )
    return {"id": uid, "email": email, "role": "admin", "token": token}


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api_router.get("/auth/me")
async def me(cu=Depends(get_current_user)):
    cu.pop("password_hash", None)
    return cu


@api_router.get("/stats")
async def get_stats(cu=Depends(get_current_user)):
    total = await db.vehicles.count_documents({})
    avail = await db.vehicles.count_documents({"status": "available"})
    featured = await db.vehicles.count_documents({"featured": True})
    home = await db.vehicles.count_documents({"show_on_home": True})
    coll_names = await db.list_collection_names()
    t_leads = await db.leads.count_documents({}) if "leads" in coll_names else 0
    new_leads = await db.leads.count_documents({"status": "new"}) if "leads" in coll_names else 0
    return {
        "total_vehicles": total,
        "available": avail,
        "featured": featured,
        "show_on_home": home,
        "total_leads": t_leads,
        "new_leads": new_leads,
    }


@api_router.get("/vehicles")
async def list_vehicles(
    make: Optional[str] = None,
    body_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    status: Optional[str] = "available",
    featured: Optional[bool] = None,
    show_on_home: Optional[bool] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "newest",
    limit: int = 20,
    skip: int = 0,
):
    q: Dict[str, Any] = {}
    if show_on_home is not None:
        q["show_on_home"] = show_on_home
    if make:
        q["make"] = {"$regex": f"^{re.escape(make)}", "$options": "i"}
    if body_type:
        q["body_type"] = {"$regex": f"^{re.escape(body_type)}", "$options": "i"}
    if status and status != "all":
        q["status"] = status
    if featured is not None:
        q["featured"] = featured
    price_q = {}
    if min_price is not None:
        price_q["$gte"] = min_price
    if max_price is not None:
        price_q["$lte"] = max_price
    if price_q:
        q["price"] = price_q
    year_q = {}
    if min_year is not None:
        year_q["$gte"] = min_year
    if max_year is not None:
        year_q["$lte"] = max_year
    if year_q:
        q["year"] = year_q
    if search:
        q["$or"] = [
            {"title": {"$regex": re.escape(search), "$options": "i"}},
            {"make": {"$regex": re.escape(search), "$options": "i"}},
            {"model": {"$regex": re.escape(search), "$options": "i"}},
            {"description": {"$regex": re.escape(search), "$options": "i"}},
            {"vin": {"$regex": re.escape(search), "$options": "i"}},
            {"stock_number": {"$regex": re.escape(search), "$options": "i"}},
        ]

    sort_map = {
        "newest": [("created_at", -1)],
        "oldest": [("created_at", 1)],
        "price_low": [("price", 1)],
        "price_high": [("price", -1)],
        "year_new": [("year", -1)],
        "mileage_low": [("mileage", 1)],
    }
    sort_spec = sort_map.get(sort or "newest", sort_map["newest"])

    total = await db.vehicles.count_documents(q)
    cursor = db.vehicles.find(q).sort(sort_spec).skip(int(skip)).limit(int(limit))
    docs = await cursor.to_list(int(limit))
    for d in docs:
        d["_id"] = str(d["_id"])
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
    return {"vehicles": docs, "total": total, "limit": limit, "skip": skip}


@api_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Look up by ObjectId, stock_number, or vin — whichever matches first."""
    doc = None
    oid = to_object_id(vehicle_id)
    if oid:
        doc = await db.vehicles.find_one({"_id": oid})
    if not doc:
        doc = await db.vehicles.find_one({
            "$or": [
                {"stock_number": vehicle_id},
                {"vin": vehicle_id.upper()},
                {"slug": vehicle_id},
            ]
        })
    if not doc:
        raise HTTPException(404, "Vehicle not found")
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


# ─── Lead capture (public) ────────────────────────────────────────
@api_router.post("/leads")
async def create_lead(data: LeadCreate):
    doc = {
        **data.model_dump(),
        "status": "new",
        "created_at": datetime.now(timezone.utc),
    }
    res = await db.leads.insert_one(doc)
    return {"id": str(res.inserted_id), "ok": True}


# ─── Admin: vehicles CRUD ─────────────────────────────────────────
@api_router.post("/vehicles")
async def create_vehicle(data: VehicleCreate, cu=Depends(get_current_user)):
    doc = {**data.model_dump(), "created_at": datetime.now(timezone.utc)}
    res = await db.vehicles.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@api_router.put("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: str, data: VehicleUpdate, cu=Depends(get_current_user)):
    oid = to_object_id(vehicle_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    upd = {k: v for k, v in data.model_dump().items() if v is not None}
    upd["updated_at"] = datetime.now(timezone.utc)
    await db.vehicles.update_one({"_id": oid}, {"$set": upd})
    doc = await db.vehicles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Vehicle not found")
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@api_router.patch("/vehicles/{vehicle_id}/toggle")
async def toggle_vehicle_flag(vehicle_id: str, payload: Dict[str, Any], cu=Depends(get_current_user)):
    """Quick-toggle endpoint for show_on_home / featured / status from the admin table."""
    oid = to_object_id(vehicle_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    allowed = {"show_on_home", "featured", "status"}
    upd = {k: v for k, v in payload.items() if k in allowed}
    if not upd:
        raise HTTPException(400, "No valid fields")
    upd["updated_at"] = datetime.now(timezone.utc)
    await db.vehicles.update_one({"_id": oid}, {"$set": upd})
    doc = await db.vehicles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Vehicle not found")
    doc["_id"] = str(doc["_id"])
    return doc


@api_router.post("/vehicles/{vehicle_id}/images")
async def replace_vehicle_images(vehicle_id: str, payload: BulkImageImport, cu=Depends(get_current_user)):
    """Bulk replace images for a vehicle from a list of URLs."""
    oid = to_object_id(vehicle_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    cleaned = []
    for raw in payload.urls:
        for piece in re.split(r"[\s,;\n]+", raw or ""):
            p = piece.strip()
            if p and p.startswith(("http://", "https://", "data:image/")):
                cleaned.append(p)
    # de-dup, preserve order
    seen = set()
    images = [u for u in cleaned if not (u in seen or seen.add(u))]
    await db.vehicles.update_one({"_id": oid}, {"$set": {"images": images, "updated_at": datetime.now(timezone.utc)}})
    return {"ok": True, "count": len(images), "images": images}


@api_router.delete("/vehicles/bulk/delete")
async def bulk_delete_vehicles(payload: BulkDeleteRequest, cu=Depends(get_current_user)):
    oids = [to_object_id(v) for v in payload.vehicle_ids]
    oids = [o for o in oids if o is not None]
    if not oids:
        raise HTTPException(400, "No valid IDs")
    res = await db.vehicles.delete_many({"_id": {"$in": oids}})
    return {"ok": True, "deleted": res.deleted_count}


@api_router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str, cu=Depends(get_current_user)):
    oid = to_object_id(vehicle_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    res = await db.vehicles.delete_one({"_id": oid})
    if not res.deleted_count:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api_router.post("/vehicles/import")
async def import_vehicles(file: UploadFile = File(...), cu=Depends(get_current_user)):
    content = await file.read()
    decoded = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))
    added = updated = 0
    for row in reader:
        try:
            raw_imgs = row.get("images", "")
            imgs = [img.strip() for img in re.split(r"[,\s\n;]+", raw_imgs) if img.strip().startswith(("http://", "https://"))]
            v = {
                "title": (row.get("title") or f"{row.get('year','')} {row.get('make','')} {row.get('model','')}".strip()).strip(),
                "make": (row.get("make") or "").strip(),
                "model": (row.get("model") or "").strip(),
                "year": int(row.get("year", 2024) or 2024),
                "price": float(row.get("price", 0) or 0),
                "mileage": int(row.get("mileage", 0) or 0),
                "condition": (row.get("condition") or "used").lower(),
                "body_type": (row.get("body_type") or "Sedan").strip(),
                "fuel_type": (row.get("fuel_type") or "Gas").strip(),
                "transmission": (row.get("transmission") or "Automatic").strip(),
                "exterior_color": (row.get("exterior_color") or "").strip(),
                "interior_color": (row.get("interior_color") or "").strip(),
                "vin": (row.get("vin") or "").strip().upper(),
                "stock_number": (row.get("stock_number") or "").strip(),
                "description": (row.get("description") or "").strip(),
                "images": imgs,
                "status": (row.get("status") or "available").lower(),
                "featured": str(row.get("featured", "")).lower() in ("true", "1", "yes"),
                "show_on_home": str(row.get("show_on_home", "")).lower() in ("true", "1", "yes"),
                "updated_at": datetime.now(timezone.utc),
            }
            if not v["vin"] and not v["stock_number"] and not v["title"]:
                continue
            key = {"vin": v["vin"]} if v["vin"] else ({"stock_number": v["stock_number"]} if v["stock_number"] else {"title": v["title"]})
            existing = await db.vehicles.find_one(key)
            if existing:
                await db.vehicles.update_one({"_id": existing["_id"]}, {"$set": v})
                updated += 1
            else:
                v["created_at"] = datetime.now(timezone.utc)
                await db.vehicles.insert_one(v)
                added += 1
        except Exception as e:
            logger.warning(f"CSV row skipped: {e}")
    return {"ok": True, "added": added, "updated": updated}


# ─── Leads ─────────────────────────────────────────────────────────
@api_router.get("/leads")
async def list_leads(cu=Depends(get_current_user)):
    if "leads" not in await db.list_collection_names():
        return []
    docs = await db.leads.find({}).sort([("created_at", -1)]).to_list(500)
    for d in docs:
        d["_id"] = str(d["_id"])
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
    return docs


@api_router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, data: LeadStatusUpdate, cu=Depends(get_current_user)):
    oid = to_object_id(lead_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    await db.leads.update_one({"_id": oid}, {"$set": {"status": data.status}})
    return {"ok": True}


@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, cu=Depends(get_current_user)):
    oid = to_object_id(lead_id)
    if not oid:
        raise HTTPException(400, "Invalid ID")
    await db.leads.delete_one({"_id": oid})
    return {"ok": True}


# ─── Scraper / external import ────────────────────────────────────
@api_router.get("/scraper/settings")
async def get_scraper_settings(cu=Depends(get_current_user)):
    settings = await db.settings.find_one({"_id": "scraper"})
    if not settings:
        return {"auto_sync": False, "last_sync": None, "source": "teamford"}
    settings["_id"] = str(settings["_id"])
    if isinstance(settings.get("last_sync"), datetime):
        settings["last_sync"] = settings["last_sync"].isoformat()
    return settings


@api_router.post("/scraper/import-url")
async def import_vehicle_from_url(data: ScraperImportRequest, cu=Depends(get_current_user)):
    raw_urls = data.url or ""
    urls = [u.strip() for u in re.split(r"[\s\n,;]+", raw_urls) if u.strip().startswith("http")]
    from scraper import scrape_teamford_listing
    results = []
    for url in urls:
        try:
            v_data = await scrape_teamford_listing(url)
            if not v_data:
                results.append({"status": "skipped", "url": url, "reason": "no data"})
                continue
            v_data["updated_at"] = datetime.now(timezone.utc)
            vin = (v_data.get("vin") or "").upper()
            existing = await db.vehicles.find_one({"vin": vin}) if vin else None
            if existing:
                await db.vehicles.update_one({"_id": existing["_id"]}, {"$set": v_data})
                results.append({"status": "updated", "url": url, "title": v_data.get("title")})
            else:
                v_data["created_at"] = datetime.now(timezone.utc)
                await db.vehicles.insert_one(v_data)
                results.append({"status": "imported", "url": url, "title": v_data.get("title")})
        except Exception as e:
            logger.error(f"Scrape failed {url}: {e}")
            results.append({"status": "error", "url": url, "reason": str(e)[:120]})
    return {"results": results, "ok": True}


# ─── Chatbot ──────────────────────────────────────────────────────
@api_router.post("/chat")
async def ai_chat(data: ChatRequest):
    try:
        # Pull top-30 vehicles so the bot has real inventory context
        docs = await db.vehicles.find({"status": "available"}).limit(60).to_list(60)
        for d in docs:
            d["_id"] = str(d["_id"])

        from scraper import NeuralKnowledge

        gemini_api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
        if gemini_api_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_api_key)
                inventory_lines = "\n".join(
                    f"• {v.get('year','')} {v.get('make','')} {v.get('model','')} — ${v.get('price',0):,.0f}"
                    f" · {v.get('mileage',0):,} km · {v.get('body_type','')}"
                    for v in docs
                )
                system = (
                    "You are 'Alpha', the AutoNorth Motors AI vehicle specialist — confident, "
                    "helpful, never pushy, and laser-focused on matching customers to the right car. "
                    "Edmonton dealership, 825-605-5050, 9104 91 St NW. Zero dealer fees. "
                    "Always use real inventory below. If asked something off-topic, gently steer back to vehicles. "
                    "Keep replies concise (3-5 sentences) unless the customer wants depth.\n\n"
                    f"LIVE INVENTORY ({len(docs)} models):\n{inventory_lines}"
                )
                chat = client.chats.create(
                    model="gemini-1.5-flash",
                    config=genai.types.GenerateContentConfig(system_instruction=system),
                )
                resp = chat.send_message(data.message)
                lead_captured = NeuralKnowledge.detect_lead_intent(data.message)
                if lead_captured:
                    await _capture_chat_lead(data)
                return {"response": resp.text, "lead_captured": lead_captured, "engine": "gemini"}
            except Exception as e:
                logger.warning(f"Gemini failed, falling back: {e}")

        # Local intelligent fallback (no API key needed)
        reply, lead_captured = NeuralKnowledge.smart_reply(data.message, docs)
        if lead_captured:
            await _capture_chat_lead(data)
        return {"response": reply, "lead_captured": lead_captured, "engine": "local"}
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {
            "response": "I'm having trouble accessing inventory right now — give us a quick call at 825-605-5050 and a specialist will help you immediately.",
            "lead_captured": False,
            "engine": "error",
        }


async def _capture_chat_lead(data: ChatRequest):
    """Persist a soft lead from the chat session for follow-up."""
    try:
        await db.leads.insert_one({
            "name": f"Chat visitor {data.session_id[:8]}",
            "lead_type": "chatbot",
            "message": data.message,
            "source": "chatbot",
            "status": "new",
            "session_id": data.session_id,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Lead capture failed: {e}")


# ─── Startup ──────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    global db
    db = await get_db(DB_NAME)
    # Ensure at least one admin exists
    if not await db.users.find_one({"email": "admin@autonorth.ca"}):
        admin_pwd = os.environ.get("ADMIN_PASSWORD", "AutoNorth2026!")
        await db.users.insert_one({
            "email": "admin@autonorth.ca",
            "password_hash": hash_password(admin_pwd),
            "role": "admin",
            "created_at": datetime.now(timezone.utc),
        })
        logger.info("Seeded default admin user (admin@autonorth.ca).")
    # Seed inventory if empty
    if await db.vehicles.count_documents({}) == 0:
        try:
            from seed_data import build_seed_vehicles
            seed = build_seed_vehicles()
            now = datetime.now(timezone.utc)
            for v in seed:
                v.setdefault("created_at", now)
            await db.vehicles.insert_many(seed)
            logger.info(f"Seeded {len(seed)} demo vehicles.")
        except Exception as e:
            logger.warning(f"Seed skipped: {e}")
    logger.info("AutoNorth API ready.")


app.include_router(api_router)
