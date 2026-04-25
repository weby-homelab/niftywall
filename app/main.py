import os
import json
import uvicorn
import psutil
import requests
import datetime as dt
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, Form, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.nft_handler import NftablesHandler
from app.auth import auth_router, get_current_user, DATA_DIR
from app.fail2ban_parser import Fail2BanParser
from app.db import get_db

app = FastAPI(title="NiftyWall")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Authentication Router
app.include_router(auth_router)

# Initialize handlers
nft = NftablesHandler()
f2b = Fail2BanParser()

# Common port to service mapping
SERVICE_MAP = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL",
    6379: "Redis", 27017: "MongoDB", 5050: "FlashMonitor", 8080: "NiftyWall",
    54322: "SSH-Alt", 3001: "UptimeKuma", 53: "DNS"
}

# Setup templates
templates = Jinja2Templates(directory="templates")

class UnbanRequest(BaseModel):
    ip: str = Field(..., pattern=r'^[\w\.\:\-\/]+$')
    jail: Optional[str] = Field(None, pattern=r'^[\w\-]+$')

class PortRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("filter", pattern=r'^[\w\-]+$')
    chain: str = Field("input", pattern=r'^[\w\-]+$')
    port: int = Field(..., ge=1, le=65535)

class NATRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("niftywall", pattern=r'^[\w\-]+$')
    chain: str = Field("nw-prerouting", pattern=r'^[\w\-]+$')
    protocol: str = Field("tcp", pattern=r'^(tcp|udp)$')
    external_port: int = Field(..., ge=1, le=65535)
    internal_ip: str = Field(..., pattern=r'^[\w\.\:\-\/]+$')
    internal_port: Optional[int] = Field(None, ge=1, le=65535)

class SetElementRequest(BaseModel):
    family: str = Field(..., pattern=r'^(ip|ip6|inet)$')
    table: str = Field(..., pattern=r'^[\w\-]+$')
    set_name: str = Field(..., pattern=r'^[\w\-]+$')
    element: str = Field(..., pattern=r'^[\w\.\:\-\/]+$')

class AdvancedRuleRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("niftywall", pattern=r'^[\w\-]+$')
    chain: str = Field("nw-input", pattern=r'^[\w\-]+$')
    protocol: str = Field("tcp", pattern=r'^(tcp|udp)$')
    ports: str = Field("", pattern=r'^[\d\,]*$')
    source: str = Field("any", pattern=r'^[\w\.\:\-\/\@]+$')
    action: str = Field("accept", pattern=r'^(accept|drop)$')
    rate_enabled: bool = False
    rate: int = Field(0, ge=0)
    unit: str = Field("second", pattern=r'^(second|minute|hour|day)$')
    burst: int = Field(0, ge=0)

def log_action(user: str, action: str, details: str):
    """Log administrative actions to a local SQLite database."""
    timestamp = datetime.now().isoformat()
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO audit_log (timestamp, username, action, details) VALUES (?, ?, ?, ?)', 
                  (timestamp, user, action, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"CRITICAL: Failed to write audit log: {e}")

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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: str = Depends(get_current_user)):
    import socket
    import os
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

@app.get("/api/system/status")
async def get_system_status(user: str = Depends(get_current_user)):
    """Return detailed system status metrics with uptime history."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            
        uptime_history = get_uptime_history(uptime_seconds)
            
        return {
            "cpu_usage": psutil.cpu_percent(interval=None),
            "memory_usage": psutil.virtual_memory().percent,
            "uptime": uptime_seconds,
            "uptime_history": uptime_history,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/whois/{ip}")
async def get_whois_info(ip: str):
    """Fetch geo/provider info for an IP."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        return r.json()
    except Exception:
        return {"status": "fail", "message": "WHOIS service unavailable"}

@app.post("/api/fail2ban/unban")
async def unban_ip(req: UnbanRequest, user: str = Depends(get_current_user)):
    """Unban an IP using fail2ban-client."""
    success = f2b.unban_ip(req.ip, req.jail)
    if success:
        log_action(user, "UNBAN", f"IP: {req.ip}, Jail: {req.jail or 'auto'}")
        return {"status": "success", "message": f"IP {req.ip} has been unbanned."}
    raise HTTPException(status_code=500, detail="Failed to unban IP. Check logs.")

@app.get("/api/ruleset")
async def get_ruleset(user: str = Depends(get_current_user)):
    try:
        data = nft.get_ruleset()
        if "error" in data:
            # Avoid leaking raw internal errors
            raise HTTPException(status_code=500, detail="Failed to fetch ruleset. Check system logs.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/ruleset/advanced")
async def add_advanced_rule(req: AdvancedRuleRequest, user: str = Depends(get_current_user)):
    try:
        res = nft.add_advanced_rule(
            family=req.family,
            table=req.table,
            chain=req.chain,
            protocol=req.protocol,
            ports=req.ports,
            source=req.source,
            action=req.action,
            rate_enabled=req.rate_enabled,
            rate=req.rate,
            unit=req.unit,
            burst=req.burst
        )
        if res["success"]:
            log_action(user, "ADD_RULE", f"New rule in {req.chain}")
            return {"status": "success", "message": "Rule applied successfully"}
        # Sanitize error message to avoid information exposure
        raise HTTPException(status_code=500, detail="Failed to apply advanced rule. Check system logs.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/api/ruleset/{family}/{table}/{chain}/{handle}")
async def delete_rule(family: str, table: str, chain: str, handle: int, user: str = Depends(get_current_user)):
    success = nft.delete_rule(family, table, chain, handle)
    if success:
        log_action(user, "DELETE_RULE", f"Handle: {handle} from {chain}")
        return {"status": "success", "message": f"Rule {handle} deleted."}
    raise HTTPException(status_code=500, detail="Failed to delete rule.")

@app.post("/api/ruleset/nat")
async def add_nat_rule(req: NATRequest, user: str = Depends(get_current_user)):
    res = nft.add_dnat_rule(
        req.family, req.table, req.chain, req.protocol,
        req.external_port, req.internal_ip, req.internal_port
    )
    if res["success"]:
        details = f"NAT: {req.protocol} {req.external_port} -> {req.internal_ip}:{req.internal_port or req.external_port}"
        log_action(user, "ADD_NAT", details)
        return {"status": "success", "message": "NAT Rule applied successfully."}
    # Sanitize error message
    raise HTTPException(status_code=500, detail="Failed to apply NAT rule. Check system logs.")

@app.post("/api/ruleset/panic")
async def panic_mode(user: str = Depends(get_current_user)):
    success = nft.apply_panic_mode()
    if success:
        log_action(user, "PANIC_MODE", "Emergency lockdown activated")
        return {"status": "success", "message": "Panic mode activated!"}
    raise HTTPException(status_code=500, detail="Failed to activate panic mode.")

@app.post("/api/ruleset/restore-panic")
async def restore_panic(user: str = Depends(get_current_user)):
    """Exit panic mode by restoring the most recent snapshot."""
    snapshots = nft.list_snapshots()
    if not snapshots:
        raise HTTPException(status_code=404, detail="No snapshots found to restore from.")
    
    # The most recent snapshot is first in the list
    latest = snapshots[0]['filename']
    success = nft.restore_snapshot(latest)
    if success:
        log_action(user, "EXIT_PANIC", f"Restored from {latest}")
        return {"status": "success", "message": "Successfully exited Panic Mode."}
    raise HTTPException(status_code=500, detail="Failed to restore snapshot.")

@app.get("/api/sets")
async def get_sets(user: str = Depends(get_current_user)):
    data = nft.get_sets()
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data

@app.post("/api/sets/element")
async def add_set_element(req: SetElementRequest, user: str = Depends(get_current_user)):
    success = nft.add_set_element(req.family, req.table, req.set_name, req.element)
    if success:
        log_action(user, "SET_ADD", f"Added {req.element} to {req.set_name}")
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to add element.")

@app.delete("/api/sets/element")
async def remove_set_element(req: SetElementRequest, user: str = Depends(get_current_user)):
    success = nft.delete_set_element(req.family, req.table, req.set_name, req.element)
    if success:
        log_action(user, "SET_REMOVE", f"Removed {req.element} from {req.set_name}")
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to remove element.")

@app.post("/api/fail2ban/info")
async def get_f2b_info(req: dict = Body(...), user: str = Depends(get_current_user)):
    """Fetch ban reasons from fail2ban."""
    info = f2b.get_ban_info_for_ips(req.get('ips', []))
    return info

@app.get("/api/snapshots")
async def get_snapshots(user: str = Depends(get_current_user)):
    return nft.list_snapshots()

@app.post("/api/snapshots/restore/{filename}")
async def restore_snapshot(filename: str, user: str = Depends(get_current_user)):
    if nft.restore_snapshot(filename):
        log_action(user, "RESTORE", f"Restored snapshot: {filename}")
        return {"status": "success", "message": f"Snapshot {filename} restored."}
    raise HTTPException(status_code=500, detail="Failed to restore snapshot.")

@app.post("/api/backup")
async def create_backup(user: str = Depends(get_current_user)):
    filename = nft._create_snapshot("manual_backup")
    if filename:
        log_action(user, "BACKUP", f"Manual backup created: {filename}")
        return {"status": "success", "message": f"Backup created: {filename}"}
    raise HTTPException(status_code=500, detail="Failed to create backup.")

@app.get("/api/audit")
async def get_audit_log(user: str = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT timestamp, username as user, action, details FROM audit_log ORDER BY id DESC LIMIT 100')
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return []

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
