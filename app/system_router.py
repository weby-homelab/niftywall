import ipaddress
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import psutil
from pydantic import BaseModel, Field
from typing import List, Optional

from app.auth import get_current_user, log_action

router = APIRouter(prefix="/api", tags=["system"])


class Fail2BanInfoRequest(BaseModel):
    ips: List[str] = Field(default_factory=list)


class Fail2BanUnbanRequest(BaseModel):
    ip: str = Field(..., min_length=3, max_length=45)
    jail: Optional[str] = Field(None, pattern=r'^[\w\-]+$')


@router.get("/system/status")
async def get_system_status(user: str = Depends(get_current_user)):
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])

        return {
            "cpu_usage": psutil.cpu_percent(interval=None),
            "memory_usage": psutil.virtual_memory().percent,
            "uptime": uptime_seconds,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/whois/{ip}")
async def get_whois_info(ip: str, user: str = Depends(get_current_user)):
    import requests
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        return r.json()
    except Exception:
        return {"status": "fail", "message": "WHOIS service unavailable"}


@router.post("/fail2ban/info")
async def get_f2b_info(req: Fail2BanInfoRequest, user: str = Depends(get_current_user)):
    from app.fail2ban_parser import Fail2BanParser
    f2b = Fail2BanParser()
    info = f2b.get_ban_info_for_ips(req.ips)
    return info


@router.post("/fail2ban/unban")
async def unban_ip(req: Fail2BanUnbanRequest, user: str = Depends(get_current_user)):
    from app.fail2ban_parser import Fail2BanParser
    f2b = Fail2BanParser()
    success = f2b.unban_ip(req.ip, req.jail)
    if success:
        log_action(user, "UNBAN", f"IP: {req.ip}, Jail: {req.jail or 'auto'}")
        return {"status": "success", "message": f"IP {req.ip} has been unbanned."}
    raise HTTPException(status_code=500, detail="Failed to unban IP. Check logs.")
