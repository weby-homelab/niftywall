from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import psutil

from app.auth import get_current_user, log_action

router = APIRouter(prefix="/api", tags=["system"])


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
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/whois/{ip}")
async def get_whois_info(ip: str):
    import requests
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        return r.json()
    except Exception:
        return {"status": "fail", "message": "WHOIS service unavailable"}


@router.post("/fail2ban/info")
async def get_f2b_info(req: dict, user: str = Depends(get_current_user)):
    from app.fail2ban_parser import Fail2BanParser
    f2b = Fail2BanParser()
    info = f2b.get_ban_info_for_ips(req.get('ips', []))
    return info


@router.post("/fail2ban/unban")
async def unban_ip(req: dict, user: str = Depends(get_current_user)):
    from app.fail2ban_parser import Fail2BanParser
    f2b = Fail2BanParser()
    success = f2b.unban_ip(req.get('ip', ''), req.get('jail'))
    if success:
        log_action(user, "UNBAN", f"IP: {req.get('ip')}, Jail: {req.get('jail', 'auto')}")
        return {"status": "success", "message": f"IP {req.get('ip')} has been unbanned."}
    raise HTTPException(status_code=500, detail="Failed to unban IP. Check logs.")
