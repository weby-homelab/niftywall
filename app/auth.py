import os
import time
import json
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Response, Form, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "niftywall-ultra-secure-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600 # 10 hours for better UX

# Users DB path
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

templates = Jinja2Templates(directory="templates")
auth_router = APIRouter()

# --- Helpers ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def has_users():
    return len(load_users()) > 0

# --- Brute Force Protection ---
failed_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 300

def check_brute_force(ip: str):
    now = time.time()
    if ip in failed_attempts:
        attempts, last_attempt = failed_attempts[ip]
        if now - last_attempt > LOCKOUT_TIME:
            failed_attempts[ip] = (0, now)
            return False
        if attempts >= MAX_ATTEMPTS:
            return True
    return False

def record_failed_attempt(ip: str):
    now = time.time()
    attempts, _ = failed_attempts.get(ip, (0, 0))
    failed_attempts[ip] = (attempts + 1, now)

def clear_failed_attempts(ip: str):
    failed_attempts.pop(ip, None)

# --- JWT ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        users = load_users()
        if username not in users:
            raise HTTPException(status_code=401, detail="User not found")
            
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

# --- Routes ---

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if not has_users():
        return RedirectResponse(url="/onboarding")
    return templates.TemplateResponse(request=request, name="login.html")

@auth_router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    
    if check_brute_force(client_ip):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Too many attempts. Locked for 5 min."})
    
    users = load_users()
    user_data = users.get(username)
    
    if not user_data or not bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
        record_failed_attempt(client_ip)
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Invalid credentials"})
    
    clear_failed_attempts(client_ip)
    access_token = create_access_token(data={"sub": username})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", 
        httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
        samesite="lax"
    )
    return response

@auth_router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request):
    if has_users():
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="onboarding.html")

@auth_router.post("/onboarding")
async def onboarding(request: Request, username: str = Form(...), password: str = Form(...)):
    if has_users():
        raise HTTPException(status_code=400, detail="Onboarding already completed")
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users = {username: {"password": hashed_password, "created_at": datetime.now().isoformat()}}
    save_users(users)
    
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@auth_router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
