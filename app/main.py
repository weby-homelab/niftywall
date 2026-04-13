import os
import json
import uvicorn
import psutil
import requests
import sqlite3
import datetime as dt
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, Form, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.nft_handler import NftablesHandler
from app.auth import auth_router, get_current_user, DATA_DIR
from app.fail2ban_parser import Fail2BanParser

app = FastAPI(title="NiftyWall")

# Include Authentication Router
app.include_router(auth_router)

# Initialize handlers
nft = NftablesHandler()
f2b = Fail2BanParser()

# Paths
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit.log")
UPTIME_HISTORY_FILE = os.path.join(DATA_DIR, "uptime_history.json")

# Common port to service mapping
SERVICE_MAP = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL",
    6379: "Redis", 27017: "MongoDB", 5050: "FlashMonitor", 8080: "NiftyWall",
    54322: "SSH-Alt", 3001: "UptimeKuma", 53: "DNS"
}

# Setup templates
templates = Jinja2Templates(directory="templates")

class UnbanRequest(BaseModel):
    ip: str
    jail: Optional[str] = None

class PortRequest(BaseModel):
    family: str = "inet"
    table: str = "filter"
    chain: str = "input"
    port: int

class NATRequest(BaseModel):
    family: str = "ip"
    table: str = "nat"
    chain: str = "prerouting"
    protocol: str = "tcp"
    external_port: int
    internal_ip: str
    internal_port: Optional[int] = None

class SetElementRequest(BaseModel):
    family: str
    table: str
    set_name: str
    element: str

def log_action(user: str, action: str, details: str):
    """Log administrative actions to a local file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | {user} | {action} | {details}\n"
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"CRITICAL: Failed to write audit log: {e}")

def get_uptime_history(current_uptime):
    """Maintain a history of daily max uptime values."""
    today = datetime.now().strftime("%Y-%m-%d")
    history = {}
    if os.path.exists(UPTIME_HISTORY_FILE):
        try:
            with open(UPTIME_HISTORY_FILE, "r") as f:
                history = json.load(f)
        except: pass
    
    # Store/Update max uptime for today
    history[today] = current_uptime
    
    # Keep only last 30 days
    sorted_dates = sorted(history.keys())
    if len(sorted_dates) > 30:
        for old_date in sorted_dates[:-30]:
            history.pop(old_date)
            
    with open(UPTIME_HISTORY_FILE, "w") as f:
        json.dump(history, f)
    
    # Return sorted values for the chart
    return [history[d] for d in sorted(history.keys())]

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
    return templates.TemplateResponse(
        request=request, name="index.html", context={"username": user}
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/whois/{ip}")
async def get_whois_info(ip: str, user: str = Depends(get_current_user)):
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
            raise HTTPException(status_code=500, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ruleset/advanced")
async def add_advanced_rule(data: dict = Body(...), user: str = Depends(get_current_user)):
    family = data.get('family', 'ip')
    chain = data.get('chain', 'input')
    if family in ['ip', 'ip6'] and chain.islower():
        chain = chain.upper()

    res = nft.add_advanced_rule(
        family=family,
        table=data.get('table', 'filter'),
        chain=chain,
        protocol=data.get('protocol', 'tcp'),
        ports=str(data.get('ports', '')),
        source=data.get('source', 'any'),
        action=data.get('action', 'accept'),
        rate_enabled=data.get('rate_enabled', False),
        rate=int(data.get('rate', 0)),
        unit=data.get('unit', 'second'),
        burst=int(data.get('burst', 0))
    )
    if res["success"]:
        log_action(user, "ADD_RULE", f"New rule in {chain}")
        return {"status": "success", "message": res["message"]}
    raise HTTPException(status_code=500, detail=res["message"])

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
    raise HTTPException(status_code=500, detail=res["message"])

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
    """Fetch ban reasons from fail2ban log for given IPs."""
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
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            lines = f.readlines()
        logs = []
        for line in reversed(lines[-100:]): # Last 100 entries
            parts = line.strip().split(" | ")
            if len(parts) == 4:
                logs.append({
                    "timestamp": parts[0],
                    "user": parts[1],
                    "action": parts[2],
                    "details": parts[3]
                })
        return logs
    except:
        return []

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
