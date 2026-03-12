from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.nft_handler import NftablesHandler
from app.auth import auth_router, get_current_user
import uvicorn

app = FastAPI(title="NFTables Dashboard")

# Include Authentication Router
app.include_router(auth_router)

# Initialize NFTables handler
nft = NftablesHandler()

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def check_auth_middleware(request: Request, call_next):
    # Allow public endpoints
    if request.url.path in ["/login", "/logout"] or request.url.path.startswith("/static/"):
        return await call_next(request)
    
    # For HTML requests (like root '/'), intercept and redirect to login if unauthorized
    if request.url.path == "/":
        try:
            get_current_user(request)
        except HTTPException:
            return RedirectResponse(url="/login", status_code=302)
            
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: str = Depends(get_current_user)):
    """Render the main dashboard."""
    return templates.TemplateResponse(
        request=request, name="index.html", context={"username": user}
    )

@app.get("/api/ruleset")
async def get_ruleset(user: str = Depends(get_current_user)):
    """API endpoint to get the current nftables ruleset in JSON."""
    data = nft.get_ruleset()
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data

@app.post("/api/backup")
async def backup_ruleset(user: str = Depends(get_current_user)):
    """API endpoint to trigger a backup."""
    success = nft.backup_ruleset()
    if success:
        return {"status": "success", "message": "Backup created successfully at /etc/nftables.conf.backup"}
    else:
        raise HTTPException(status_code=500, detail="Backup failed")

if __name__ == "__main__":
    # For local testing. In production use gunicorn/uvicorn systemd service.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
