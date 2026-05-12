from fastapi import APIRouter, HTTPException, Depends
import psutil
import os
import signal
import asyncio
from typing import List, Dict

router = APIRouter(prefix="/api/panic", tags=["panic"])

# Global state for Auto-Panic
AUTO_PANIC_ENABLED = False
# We keep track of auto-frozen processes to avoid spamming
FROZEN_PIDS = set()

def get_safe_processes() -> List[Dict]:
    procs = []
    # Whitelist: self, systemd(1), kernel workers(ppid 2)
    my_pid = os.getpid()
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'ppid']):
        try:
            info = p.info
            # Safe parsing
            pid = info['pid']
            if pid in (0, 1) or pid == my_pid or info['ppid'] == 2:
                continue
            procs.append({
                "pid": pid,
                "name": info['name'],
                "cpu": round(info['cpu_percent'] or 0.0, 1),
                "ram": round(info['memory_percent'] or 0.0, 1),
                "status": info['status']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # Sort by CPU descending
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    return procs[:15]

@router.get("/processes")
async def list_processes():
    return {"processes": get_safe_processes()}

@router.post("/freeze/{pid}")
async def freeze_process(pid: int):
    my_pid = os.getpid()
    if pid in (0, 1) or pid == my_pid:
        raise HTTPException(status_code=400, detail="Cannot freeze critical system process.")
    try:
        p = psutil.Process(pid)
        if p.ppid() == 2:
            raise HTTPException(status_code=400, detail="Cannot freeze kernel threads.")
        os.kill(pid, signal.SIGSTOP)
        return {"status": "success", "message": f"Process {pid} frozen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume/{pid}")
async def resume_process(pid: int):
    try:
        os.kill(pid, signal.SIGCONT)
        FROZEN_PIDS.discard(pid)
        return {"status": "success", "message": f"Process {pid} resumed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    return {"enabled": AUTO_PANIC_ENABLED}

@router.post("/toggle")
async def toggle_auto_panic():
    global AUTO_PANIC_ENABLED
    AUTO_PANIC_ENABLED = not AUTO_PANIC_ENABLED
    return {"enabled": AUTO_PANIC_ENABLED}

async def auto_panic_daemon():
    while True:
        try:
            if AUTO_PANIC_ENABLED:
                total_cpu = psutil.cpu_percent(interval=1.0)
                if total_cpu > 95.0:
                    procs = get_safe_processes()
                    if procs:
                        top_proc = procs[0]
                        if top_proc['cpu'] > 80.0 and top_proc['pid'] not in FROZEN_PIDS:
                            os.kill(top_proc['pid'], signal.SIGSTOP)
                            FROZEN_PIDS.add(top_proc['pid'])
                            # Import the local notification logic if available (e.g. from main or auth)
                            # For simplicity, we just print here, but it can be wired to TG
                            print(f"❄️ [PanicMode] Auto-Frozen {top_proc['name']} ({top_proc['pid']}) at {top_proc['cpu']}% CPU")
        except Exception as e:
            print(f"Auto-panic error: {e}")
        await asyncio.sleep(5)
