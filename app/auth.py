import os
import time
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default-insecure-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").encode('utf-8')

templates = Jinja2Templates(directory="templates")
auth_router = APIRouter()

# Simple In-Memory Brute Force Protection
failed_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 300 # 5 minutes

def check_brute_force(ip: str):
    now = time.time()
    if ip in failed_attempts:
        attempts, last_attempt = failed_attempts[ip]
        if now - last_attempt > LOCKOUT_TIME:
            failed_attempts[ip] = (0, now) # Reset
            return False
        if attempts >= MAX_ATTEMPTS:
            return True
    return False

def record_failed_attempt(ip: str):
    now = time.time()
    if ip in failed_attempts:
        attempts, _ = failed_attempts[ip]
        failed_attempts[ip] = (attempts + 1, now)
    else:
        failed_attempts[ip] = (1, now)

def clear_failed_attempts(ip: str):
    if ip in failed_attempts:
        del failed_attempts[ip]

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
        if username is None or username != ADMIN_USERNAME:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@auth_router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Retrieve client IP considering potential proxy (like Cloudflared)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    if check_brute_force(client_ip):
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "Too many failed attempts. Try again in 5 minutes."}
        )
    
    # Check credentials
    if username != ADMIN_USERNAME or not bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH):
        record_failed_attempt(client_ip)
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "Invalid username or password"}
        )
    
    clear_failed_attempts(client_ip)
    access_token = create_access_token(data={"sub": username})
    
    # Redirect to home and set cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
        secure=False, # Set to True if using HTTPS
        samesite="lax"
    )
    return response

@auth_router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
