"""
SQLite mock database for Luminara Med Spa appointment system.
Providers, treatments, availability, and bookings.
"""
import sqlite3
import random
import string
from datetime import date, datetime, timedelta
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "medspa.db"

# Clinic hours: Mon-Sat 9am-5pm
_OPEN_DAYS = {0, 1, 2, 3, 4, 5}
_SLOT_TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

# Provider specialties (who does what)
_PROVIDERS = {
    "Dr. Sarah Chen": {
        "title": "Medical Director",
        "specialties": ["Morpheus8", "PDO Threads", "Sculptra", "Kybella",
                        "Botox", "Dermal Fillers"],
        "slot_duration_min": 60,
    },
    "Jennifer Walsh, RN": {
        "title": "Aesthetic Nurse Injector",
        "specialties": ["Botox", "Dysport", "Dermal Fillers", "Kybella"],
        "slot_duration_min": 45,
    },
    "Michelle Torres": {
        "title": "Licensed Medical Aesthetician",
        "specialties": ["HydraFacial", "Chemical Peels", "IPL Photofacial",
                        "Laser Hair Removal"],
        "slot_duration_min": 60,
    },
}

_TREATMENT_INFO = {
    "Botox": {
        "description": "Neuromodulator injections to soften lines and wrinkles.",
        "areas": "Forehead, frown lines, crow's feet, brow lift, lip lines, neck bands.",
        "duration": "15-30 minutes.",
        "downtime": "Minimal. Avoid exercise and lying down for 4 hours.",
        "results": "Visible in 3-5 days, full effect at 2 weeks. Lasts 3-4 months.",
        "starting_price": 300,
        "provider": "Jennifer Walsh, RN",
    },
    "Dysport": {
        "description": "Botox alternative — spreads slightly wider, preferred for forehead and crow's feet.",
        "duration": "15-30 minutes.",
        "downtime": "Minimal.",
        "results": "Sometimes visible faster than Botox (2-3 days). Lasts 3-5 months.",
        "starting_price": 300,
        "provider": "Jennifer Walsh, RN",
    },
    "Dermal Fillers": {
        "description": "Hyaluronic acid injections to restore volume, contour cheeks, and enhance lips.",
        "areas": "Lips, cheeks, nasolabial folds, jawline, under-eye hollows.",
        "duration": "30-60 minutes.",
        "downtime": "Mild swelling and bruising for 2-5 days.",
        "results": "Immediate. Lasts 9-18 months depending on area.",
        "starting_price": 650,
        "provider": "Jennifer Walsh, RN",
    },
    "Morpheus8": {
        "description": "FDA-cleared radiofrequency microneedling — tightens skin and reduces fat.",
        "areas": "Face, neck, abdomen, arms, thighs.",
        "duration": "60-90 minutes.",
        "downtime": "3-5 days of redness and pinpoint marks. Avoid sun exposure.",
        "results": "Improves over 3 months as collagen remodels. Lasts 1-3 years.",
        "starting_price": 1200,
        "provider": "Dr. Sarah Chen",
    },
    "Kybella": {
        "description": "Injectable deoxycholic acid that permanently destroys submental fat (double chin).",
        "duration": "20-30 minutes per session.",
        "downtime": "Significant swelling for 1-2 weeks. Expect 2-6 sessions.",
        "results": "Permanent fat cell destruction. Results fully visible after series.",
        "starting_price": 800,
        "provider": "Dr. Sarah Chen",
    },
    "HydraFacial": {
        "description": "Three-step medical-grade facial: cleanse + exfoliate, extract, hydrate.",
        "duration": "30-60 minutes.",
        "downtime": "None. Skin glows immediately.",
        "results": "Instant radiance. Recommended monthly for maintenance.",
        "starting_price": 200,
        "provider": "Michelle Torres",
    },
    "Chemical Peels": {
        "description": "Controlled acid exfoliation to improve texture, tone, and acne scarring.",
        "depth": "Light, medium, or deep depending on concern.",
        "duration": "30-45 minutes.",
        "downtime": "Light: none. Medium: 3-7 days peeling. Deep: 1-2 weeks.",
        "results": "One to a series depending on depth. Improves over 2-4 weeks.",
        "starting_price": 150,
        "provider": "Michelle Torres",
    },
    "IPL Photofacial": {
        "description": "Intense pulsed light to treat sun damage, redness, and hyperpigmentation.",
        "duration": "20-30 minutes.",
        "downtime": "Mild redness, spots may darken before flaking off over 7-10 days.",
        "results": "Series of 3-5 recommended. Significant improvement by session 3.",
        "starting_price": 350,
        "provider": "Michelle Torres",
    },
    "PDO Threads": {
        "description": "Dissolvable sutures placed under the skin to lift sagging tissue.",
        "areas": "Brows, midface, jowls, neck.",
        "duration": "45-75 minutes.",
        "downtime": "1 week: avoid chewing hard foods, massage, and strenuous exercise.",
        "results": "Immediate lift with collagen building over 3 months. Lasts 12-18 months.",
        "starting_price": 1500,
        "provider": "Dr. Sarah Chen",
    },
    "Sculptra": {
        "description": "Poly-L-lactic acid biostimulator — gradually restores lost facial volume.",
        "duration": "45-60 minutes per session.",
        "downtime": "Mild swelling. Massage treated area for 5 days after.",
        "results": "Gradual — builds over 3 months. Series of 2-3 vials. Lasts 2+ years.",
        "starting_price": 800,
        "provider": "Dr. Sarah Chen",
    },
    "Laser Hair Removal": {
        "description": "Permanent hair reduction using targeted laser energy.",
        "areas": "Legs, underarms, bikini, face, back, arms — any body area.",
        "duration": "15-90 minutes depending on area.",
        "downtime": "None. Avoid sun exposure before and after.",
        "results": "Series of 6-8 sessions spaced 6 weeks apart. 80-90% permanent reduction.",
        "starting_price": 100,
        "provider": "Michelle Torres",
    },
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _gen_code() -> str:
    return "LMS" + "".join(random.choices(string.digits, k=4))


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT DEFAULT '',
            treatment TEXT NOT NULL,
            provider TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            notes TEXT DEFAULT '',
            confirmed_at TEXT NOT NULL,
            confirmation_code TEXT NOT NULL UNIQUE
        )
    """)
    if cur.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
        _seed(cur)
    conn.commit()
    conn.close()


def _seed(cur) -> None:
    today = date.today()
    samples = [
        ("Adams, Laura", "ladams@email.com", "540-555-0211", "HydraFacial", "Michelle Torres", 0, "10:00", ""),
        ("Bennett, Chloe", "cbennett@email.com", "540-555-0232", "Botox", "Jennifer Walsh, RN", 1, "14:00", "First time — nervous about needles"),
        ("Carter, Diana", "dcarter@email.com", "540-555-0243", "Morpheus8", "Dr. Sarah Chen", 1, "09:00", "Neck and face treatment"),
        ("Evans, Morgan", "mevans@email.com", "540-555-0254", "Dermal Fillers", "Jennifer Walsh, RN", 2, "11:00", "Lip enhancement consult"),
        ("Foster, Natalie", "nfoster@email.com", "540-555-0265", "Chemical Peels", "Michelle Torres", 3, "13:00", ""),
    ]
    for name, email, phone, treatment, provider, day_off, time, notes in samples:
        d = today + timedelta(days=day_off)
        if d.weekday() not in _OPEN_DAYS:
            d += timedelta(days=1)
        cur.execute("""
            INSERT INTO appointments (name, email, phone, treatment, provider, date, time, notes, confirmed_at, confirmation_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, treatment, provider, d.isoformat(), time, notes,
              datetime.now().isoformat(), _gen_code()))


def _provider_for_treatment(treatment: str) -> str:
    for provider, info in _PROVIDERS.items():
        if treatment in info["specialties"]:
            return provider
    return "Dr. Sarah Chen"


def get_available_slots(treatment: str, preferred_date: str | None = None) -> dict:
    """Return available slots for a treatment, defaulting to next 3 available days."""
    provider = _provider_for_treatment(treatment)
    start = date.today() + timedelta(days=1)
    if preferred_date:
        try:
            start = date.fromisoformat(preferred_date)
        except ValueError:
            pass

    conn = get_conn()
    results = []
    d = start
    for _ in range(14):  # search up to 14 days ahead
        if d.weekday() in _OPEN_DAYS:
            booked_times = {row["time"] for row in conn.execute(
                "SELECT time FROM appointments WHERE date = ? AND provider = ?",
                (d.isoformat(), provider)
            ).fetchall()}
            open_slots = [t for t in _SLOT_TIMES if t not in booked_times]
            if open_slots:
                results.append({"date": d.isoformat(), "available_times": open_slots})
            if len(results) >= 3:
                break
        d += timedelta(days=1)
    conn.close()
    return {
        "treatment": treatment,
        "provider": provider,
        "availability": results,
        "note": "We're open Monday through Saturday, 9 AM to 5 PM.",
    }


def create_appointment(name: str, email: str, phone: str, treatment: str,
                        for_date: str, time: str, notes: str) -> dict:
    provider = _provider_for_treatment(treatment)
    code = _gen_code()
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO appointments (name, email, phone, treatment, provider, date, time, notes, confirmed_at, confirmation_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, treatment, provider, for_date, time, notes,
              datetime.now().isoformat(), code))
        conn.commit()
        return {
            "success": True,
            "confirmation_code": code,
            "treatment": treatment,
            "provider": provider,
            "date": for_date,
            "time": time,
            "name": name,
        }
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Please retry — confirmation code collision."}
    finally:
        conn.close()


def find_appointment(lookup: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT name, treatment, provider, date, time, notes, confirmation_code
        FROM appointments
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY date, time
        LIMIT 5
    """, (f"%{lookup}%", f"%{lookup}%", f"%{lookup}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_treatment_details(treatment: str) -> dict:
    # Try exact match first, then case-insensitive
    info = _TREATMENT_INFO.get(treatment)
    if not info:
        for key, val in _TREATMENT_INFO.items():
            if key.lower() == treatment.lower():
                info = val
                treatment = key
                break
    if not info:
        # Partial match
        for key, val in _TREATMENT_INFO.items():
            if treatment.lower() in key.lower():
                info = val
                treatment = key
                break
    if not info:
        return {
            "found": False,
            "message": f"No treatment info found for '{treatment}'. Available treatments: {', '.join(_TREATMENT_INFO.keys())}",
        }
    return {"found": True, "treatment": treatment, **info}
