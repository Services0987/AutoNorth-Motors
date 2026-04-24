"""
AutoNorth scraper + zero-cost intelligent chatbot fallback.

- `scrape_teamford_listing(url)`: pulls vehicle data from a teamford.ca VDP.
- `NeuralKnowledge.smart_reply(msg, inventory)`: rules-based AI specialist
  used when no Gemini API key is configured.
"""
from __future__ import annotations

import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# ───────────────────────── Scraper ─────────────────────────────────


async def scrape_teamford_listing(url: str) -> Optional[Dict[str, Any]]:
    """Best-effort HTML scrape. Returns vehicle dict or None."""
    if not url.startswith("http"):
        return None
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": UA}) as cx:
            r = await cx.get(url)
            if r.status_code >= 400:
                return None
            html = r.text
    except Exception as e:
        logger.warning(f"Fetch failed {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    def first_text(*selectors):
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(" ", strip=True)
        return ""

    title = first_text("h1", '[class*="vehicle-title"]', '[class*="vdp-title"]', "title")
    price_text = first_text('[class*="price"]', '[data-price]')
    price = _parse_int(price_text)
    year = _parse_year(title)
    make_model = re.sub(r"^\s*\d{4}\s*", "", title).strip()
    parts = make_model.split()
    make = parts[0] if parts else ""
    model = " ".join(parts[1:3]) if len(parts) > 1 else ""

    # collect images
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if src.startswith("http") and not any(k in src for k in ("logo", "icon", "sprite")):
            if src not in imgs:
                imgs.append(src)
        if len(imgs) >= 20:
            break

    vin = ""
    m = re.search(r"\bVIN[:\s]*([A-HJ-NPR-Z0-9]{17})", html, re.I)
    if m:
        vin = m.group(1).upper()

    stock = ""
    m = re.search(r"\bStock(?: ?#|:)\s*([A-Z0-9-]+)", html, re.I)
    if m:
        stock = m.group(1)

    mileage = 0
    m = re.search(r"([\d,]+)\s*km", html, re.I)
    if m:
        mileage = _parse_int(m.group(1))

    if not (title or vin or price):
        return None

    return {
        "title": title or f"{year or ''} {make} {model}".strip(),
        "make": make,
        "model": model,
        "year": year or 2024,
        "price": price or 0,
        "mileage": mileage,
        "vin": vin,
        "stock_number": stock,
        "images": imgs[:15],
        "status": "available",
        "source_url": url,
        "imported_at": datetime.now(timezone.utc),
    }


def _parse_int(s: str) -> int:
    if not s:
        return 0
    nums = re.sub(r"[^\d]", "", s)
    return int(nums) if nums else 0


def _parse_year(s: str) -> Optional[int]:
    m = re.search(r"\b(19|20)\d{2}\b", s or "")
    return int(m.group(0)) if m else None


# ───────────────────── Local intelligent chatbot ───────────────────


class NeuralKnowledge:
    """Zero-cost intelligent chatbot. Understands intent and inventory."""

    GREETINGS = ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "yo", "howdy")
    LEAD_INTENTS = ("test drive", "book", "appointment", "visit", "see it", "come in", "buy", "interested",
                    "call me", "contact me", "purchase", "trade in", "trade-in", "financing", "pre-approved",
                    "pre approval", "preapproval", "schedule")
    BUY_PHRASES = ("looking for", "need a", "want a", "show me", "find me", "search for", "do you have",
                   "any", "got any", "available")

    BODY_KEYWORDS = {
        "truck": "Truck", "trucks": "Truck", "pickup": "Truck", "f-150": "Truck", "f150": "Truck",
        "suv": "SUV", "suvs": "SUV", "explorer": "SUV", "edge": "SUV", "escape": "SUV", "expedition": "SUV",
        "sedan": "Sedan", "sedans": "Sedan", "fusion": "Sedan",
        "coupe": "Coupe", "mustang": "Coupe", "sports car": "Coupe",
        "van": "Van", "transit": "Van", "cargo": "Van",
    }

    FUEL_KEYWORDS = {
        "electric": "Electric", "ev": "Electric", "tesla": "Electric",
        "hybrid": "Hybrid", "plug-in": "Hybrid", "phev": "Hybrid",
        "diesel": "Diesel",
        "gas": "Gas", "gasoline": "Gas", "petrol": "Gas",
    }

    # ── Public entry point ────────────────────────────────────────
    @classmethod
    def smart_reply(cls, message: str, inventory: List[Dict[str, Any]]) -> Tuple[str, bool]:
        msg = (message or "").lower().strip()
        if not msg:
            return ("Tell me what you're looking for — a truck, SUV, EV, family ride? "
                    "I'll show you what we have in stock right now.", False)

        lead_captured = cls.detect_lead_intent(msg)

        # Greeting
        if any(msg.startswith(g) for g in cls.GREETINGS) and len(msg.split()) <= 4:
            return (
                "Hey! Welcome to AutoNorth Motors in Edmonton. I know every vehicle on our lot — "
                "what kind of ride are you looking for? Trucks, SUVs, EVs, family sedans? "
                "Or tell me your budget and I'll match you up.", lead_captured)

        # Pricing / financing intent
        if any(k in msg for k in ("financing", "finance", "loan", "monthly", "payment", "credit", "approval")):
            return (
                "We get every credit profile approved — typically in under 10 minutes. "
                "Best part: zero dealer fees, ever. Want me to send you the financing application, "
                "or pair you with a vehicle in your monthly budget? Tell me your target payment.",
                True)

        # Test drive / buy intent
        if any(k in msg for k in cls.LEAD_INTENTS):
            top = cls._top_matches(msg, inventory, limit=3)
            lines = "\n".join(cls._format_card(v) for v in top) or "Browse our full inventory at /inventory."
            return (
                "Excellent — let's get you behind the wheel. Drop your name and best phone "
                "number and I'll have a specialist call you within the hour. "
                "Or call us now at 825-605-5050.\n\n"
                f"Here are great matches for you:\n{lines}", True)

        # Contact / hours
        if any(k in msg for k in ("hours", "open", "address", "location", "where", "direction")):
            return (
                "We're at 9104 91 St NW, Edmonton, AB. Open Mon-Fri 9am-8pm, Sat-Sun 10am-6pm. "
                "Call us at 825-605-5050 or come in for a no-pressure visit.", lead_captured)

        # Inventory query — most common
        candidates = cls._top_matches(msg, inventory, limit=4)
        if candidates:
            intro = cls._intent_intro(msg)
            cards = "\n".join(cls._format_card(v) for v in candidates)
            tail = "\n\nWant to schedule a test drive on any of these? Just say the word — or ask me anything about specs, financing, or trade-ins."
            return (f"{intro}\n\n{cards}{tail}", lead_captured)

        # Out-of-stock or no match — soft sell
        return (
            "I don't see an exact match in stock today, but we get new inventory every week. "
            "Tell me your must-haves (body type, year, budget, mileage) and I'll alert you the moment it lands. "
            "Or call 825-605-5050 and we'll source the right vehicle for you.", lead_captured)

    @classmethod
    def detect_lead_intent(cls, message: str) -> bool:
        m = (message or "").lower()
        return any(k in m for k in cls.LEAD_INTENTS) or bool(re.search(r"\b\d{3}[-.\s]?\d{3,4}\b", m))

    # ── Helpers ───────────────────────────────────────────────────
    @classmethod
    def _intent_intro(cls, msg: str) -> str:
        if "under" in msg or "less than" in msg or "below" in msg:
            return "Here's what fits your budget right now:"
        if any(k in cls.BODY_KEYWORDS for k in msg.split()):
            return "Great choice — these are the strongest options on the lot:"
        if any(k in msg for k in ("family", "kids", "spacious", "room", "seats")):
            return "For family-friendly comfort and space, I'd point you here:"
        if any(k in msg for k in ("fast", "performance", "sport", "powerful", "v8")):
            return "If you want power and presence, look at these:"
        if any(k in msg for k in ("efficient", "fuel", "mileage", "economy", "ev", "electric", "hybrid")):
            return "Fuel-efficient picks built for Alberta winters:"
        return "Here are some excellent matches from our current inventory:"

    @classmethod
    def _format_card(cls, v: Dict[str, Any]) -> str:
        price = v.get("price") or 0
        miles = v.get("mileage") or 0
        return (
            f"• {v.get('year','')} {v.get('make','')} {v.get('model','')} — "
            f"${price:,.0f} · {miles:,} km · {v.get('body_type','')}"
        )

    @classmethod
    def _top_matches(cls, msg: str, inventory: List[Dict[str, Any]], limit: int = 4) -> List[Dict[str, Any]]:
        if not inventory:
            return []

        body = None
        for kw, b in cls.BODY_KEYWORDS.items():
            if kw in msg:
                body = b
                break

        fuel = None
        for kw, f in cls.FUEL_KEYWORDS.items():
            if kw in msg:
                fuel = f
                break

        budget = None
        m = re.search(r"\$?\s*(\d{1,3}(?:[,\s]?\d{3})+|\d+\s*k)", msg)
        if m:
            raw = m.group(1).replace(",", "").replace(" ", "")
            if raw.endswith("k"):
                budget = int(raw[:-1]) * 1000
            elif raw.isdigit():
                budget = int(raw)

        def score(v):
            s = 0
            if body and (v.get("body_type") or "").lower() == body.lower():
                s += 10
            if fuel and (v.get("fuel_type") or "").lower() == fuel.lower():
                s += 6
            price = v.get("price") or 0
            if budget and price and price <= budget:
                s += 5
                # closer to budget = better fit
                s += max(0, 4 - abs(budget - price) // 5000)
            # term matching against title
            title = (v.get("title") or "").lower()
            for token in re.findall(r"[a-z]{3,}", msg):
                if token in title:
                    s += 1
            if v.get("featured"):
                s += 1
            return s

        scored = sorted(inventory, key=score, reverse=True)
        # Filter out zero-score if we have any positives
        positives = [v for v in scored if score(v) > 0]
        return (positives or scored)[:limit]

    # Backward-compat shim used elsewhere
    @classmethod
    def generate_response(cls, message: str, inventory: List[Dict[str, Any]]) -> str:
        reply, _ = cls.smart_reply(message, inventory)
        return reply
