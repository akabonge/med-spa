from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.router import router
from app.tools.mock_db import init_db

app = FastAPI(title="Luminara Med Spa — Luna AI")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

_frontend = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(_frontend)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(_frontend / "index.html"))


@app.get("/admin")
async def admin_page():
    return FileResponse(str(_frontend / "admin.html"))


@app.get("/api/admin/data")
async def admin_data(key: str = ""):
    from app.config import get_settings
    from app.tools.mock_db import get_conn, _TREATMENT_INFO
    from datetime import date as _date
    from fastapi.responses import JSONResponse
    settings = get_settings()
    if key != settings.admin_key:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    conn = get_conn()
    appts = conn.execute("SELECT * FROM appointments ORDER BY date ASC, time ASC").fetchall()
    conn.close()
    today = _date.today().isoformat()
    data = [dict(a) for a in appts]
    revenue = sum(_TREATMENT_INFO.get(a["treatment"], {}).get("starting_price", 0) for a in data)
    return JSONResponse({
        "stats": {
            "total": len(data),
            "today": sum(1 for a in data if a.get("date") == today),
            "upcoming": sum(1 for a in data if a.get("date", "") >= today),
            "revenue_potential": revenue,
        },
        "appointments": data,
        "providers": ["Dr. Sarah Chen", "Jennifer Walsh, RN", "Michelle Torres"],
    })


@app.get("/dashboard")
async def dashboard():
    return FileResponse(str(_frontend / "dashboard.html"))
