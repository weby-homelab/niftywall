import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from datetime import datetime

from app.auth import get_current_user
from app.db import get_db
from app.panic_router import router as panic_router, auto_panic_daemon
from app.rules_router import router as rules_router
from app.system_router import router as system_router
from app.backup_router import router as backup_router
from app.settings_router import router as settings_router

app = FastAPI(title="NiftyWall", version="3.2.3")

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r: r.status_code(429))
app.add_middleware(SlowAPIMiddleware)

# --- Mount Static Files ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Include Routers ---
app.include_router(panic_router)
app.include_router(rules_router)
app.include_router(system_router)
app.include_router(backup_router)
app.include_router(settings_router)

# --- Startup ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_panic_daemon())

# --- Common port to service mapping ---
SERVICE_MAP = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL",
    6379: "Redis", 27017: "MongoDB", 5050: "FlashMonitor", 8080: "NiftyWall",
    54322: "SSH-Alt", 3001: "UptimeKuma", 53: "DNS"
}

# --- Setup templates ---
templates = Jinja2Templates(directory="templates")


# --- Auth Middleware ---
@app.middleware("http")
async def check_auth_middleware(request: Request, call_next):
    if request.url.path in ["/login", "/logout", "/onboarding"] or request.url.path.startswith("/static/"):
        return await call_next(request)

    if request.url.path == "/":
        try:
            get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/login")

    return await call_next(request)


# --- Root Page ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: str = Depends(get_current_user)):
    import socket
    hostname = socket.gethostname()
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
    try:
        with open(version_file, "r") as f:
            app_version = f.read().strip()
    except FileNotFoundError:
        app_version = "unknown"

    return templates.TemplateResponse(
        request=request, name="index.html", context={"username": user, "hostname": hostname, "app_version": app_version}
    )


# --- Uptime History ---
def get_uptime_history(current_uptime):
    """Maintain a history of daily max uptime values in SQLite."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO uptime_history (date, uptime) VALUES (?, ?)', (today, current_uptime))
        c.execute('DELETE FROM uptime_history WHERE date <= date("now", "-30 days")')
        conn.commit()
        c.execute('SELECT uptime FROM uptime_history ORDER BY date ASC')
        rows = c.fetchall()
        conn.close()
        return [row['uptime'] for row in rows]
    except Exception as e:
        print(f"Failed uptime: {e}")
        return [current_uptime]


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
