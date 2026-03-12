import os
import json
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any

from app.nft_handler import NftablesHandler
from app.auth import auth_router, get_current_user

app = FastAPI(title="NiftyWall")

# Include Authentication Router
app.include_router(auth_router)

# Initialize NFTables handler
nft = NftablesHandler()

# Setup templates
templates = Jinja2Templates(directory="templates")

AUDIT_LOG_FILE = "audit.log"

class PortRequest(BaseModel):
    family: str = "inet"
    table: str = "filter"
    chain: str = "input"
    port: int
    protocol: str = "tcp"

class SetElementRequest(BaseModel):
    family: str
    table: str
    set_name: str
    element: str

def log_action(user: str, action: str, details: str):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "user": user,
        "action": action,
        "details": details
    }
    try:
        print(f"AUDIT LOGGING: {action} by {user}")
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"CRITICAL: Failed to write audit log: {e}")

@app.middleware("http")
async def check_auth_middleware(request: Request, call_next):
    if request.url.path in ["/login", "/logout"] or request.url.path.startswith("/static/"):
        return await call_next(request)
    
    if request.url.path == "/":
        try:
            get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/login", status_code=302)
            
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"username": user}
    )

@app.get("/api/ruleset")
async def get_ruleset(user: str = Depends(get_current_user)):
    try:
        data = nft.get_ruleset()
        if "error" in data:
            raise HTTPException(status_code=500, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup")
async def backup_ruleset(user: str = Depends(get_current_user)):
    success = nft.backup_ruleset()
    if success:
        log_action(user, "BACKUP", "Created /etc/nftables.conf.backup")
        return {"status": "success", "message": "Backup created successfully at /etc/nftables.conf.backup"}
    raise HTTPException(status_code=500, detail="Backup failed")

@app.delete("/api/ruleset/{family}/{table}/{chain}/{handle}")
async def delete_rule(family: str, table: str, chain: str, handle: int, user: str = Depends(get_current_user)):
    success = nft.delete_rule(family, table, chain, handle)
    if success:
        log_action(user, "DELETE_RULE", f"Removed rule {handle} from {family} {table} {chain}")
        return {"status": "success", "message": f"Rule {handle} deleted successfully."}
    raise HTTPException(status_code=500, detail="Failed to delete rule.")

@app.post("/api/ruleset/port")
async def add_port(req: PortRequest, user: str = Depends(get_current_user)):
    success = nft.add_port_rule(req.family, req.table, req.chain, req.port, req.protocol)
    if success:
        log_action(user, "OPEN_PORT", f"Opened {req.port}/{req.protocol} in {req.chain}")
        return {"status": "success", "message": f"Port {req.port}/{req.protocol} opened successfully."}
    raise HTTPException(status_code=500, detail="Failed to open port.")

@app.post("/api/ruleset/panic")
async def panic_mode(user: str = Depends(get_current_user)):
    success = nft.apply_panic_mode()
    if success:
        log_action(user, "PANIC_MODE", "Emergency lockdown activated")
        return {"status": "success", "message": "Panic mode activated!"}
    raise HTTPException(status_code=500, detail="Failed to activate panic mode.")

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
        return {"status": "success", "message": f"Added {req.element} to {req.set_name}"}
    raise HTTPException(status_code=500, detail="Failed to add element")

@app.delete("/api/sets/element")
async def delete_set_element(req: SetElementRequest, user: str = Depends(get_current_user)):
    success = nft.delete_set_element(req.family, req.table, req.set_name, req.element)
    if success:
        log_action(user, "SET_REMOVE", f"Removed {req.element} from {req.set_name}")
        return {"status": "success", "message": f"Removed {req.element} from {req.set_name}"}
    raise HTTPException(status_code=500, detail="Failed to remove element")

@app.get("/api/audit")
async def get_audit_log(user: str = Depends(get_current_user)):
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "r") as f:
            for line in f:
                logs.append(json.loads(line))
    return logs[::-1]

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
