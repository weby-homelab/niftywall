from fastapi import APIRouter, HTTPException, Depends
import psutil
import os
import signal
import asyncio
from typing import List, Dict
from app.db import get_db

router = APIRouter(prefix="/api/panic", tags=["panic"])

# We keep track of auto-frozen processes to avoid spamming
FROZEN_PIDS = set()

def get_auto_panic_state() -> bool:
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = 'auto_panic_enabled'")
        row = c.fetchone()
        conn.close()
        return row[0] == 'true' if row else False
    except:
        return False

def set_auto_panic_state(enabled: bool):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('auto_panic_enabled', ?)", ('true' if enabled else 'false',))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to save auto-panic state: {e}")

def get_safe_processes(limit: int = 15) -> List[Dict]:
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
    # Sort by: frozen first, then CPU descending
    procs.sort(key=lambda x: (0 if x['status'] == 'stopped' else 1, -x['cpu']))
    return procs[:limit] if limit else procs

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
    return {"enabled": get_auto_panic_state()}

@router.post("/toggle")
async def toggle_auto_panic():
    current = get_auto_panic_state()
    new_state = not current
    set_auto_panic_state(new_state)
    return {"enabled": new_state}

async def auto_panic_daemon():
    while True:
        try:
            if get_auto_panic_state():
                total_cpu = psutil.cpu_percent(interval=1.0)
                total_ram = psutil.virtual_memory().percent
                
                if total_cpu > 95.0 or total_ram > 95.0:
                    procs = get_safe_processes(limit=0) # Get all to find RAM hog
                    running_procs = [p for p in procs if p['status'] != 'stopped']
                    
                    if total_cpu > 95.0:
                        # Highest CPU (running_procs is sorted by CPU due to get_safe_processes)
                        top_cpu_proc = next(iter(running_procs), None)
                        if top_cpu_proc and top_cpu_proc['cpu'] > 80.0 and top_cpu_proc['pid'] not in FROZEN_PIDS:
                            os.kill(top_cpu_proc['pid'], signal.SIGSTOP)
                            FROZEN_PIDS.add(top_cpu_proc['pid'])
                            print(f"❄️ [PanicMode] Auto-Frozen {top_cpu_proc['name']} ({top_cpu_proc['pid']}) at {top_cpu_proc['cpu']}% CPU")
                    
                    if total_ram > 95.0:
                        # Find highest RAM process
                        top_ram_proc = max(running_procs, key=lambda x: x['ram'], default=None)
                        if top_ram_proc and top_ram_proc['ram'] > 30.0:
                            os.kill(top_ram_proc['pid'], signal.SIGKILL)
                            # Remove from frozen list if it was there just in case
                            FROZEN_PIDS.discard(top_ram_proc['pid'])
                            print(f"🚨 [PanicMode] Auto-Killed {top_ram_proc['name']} ({top_ram_proc['pid']}) at {top_ram_proc['ram']}% RAM to free memory")
        except Exception as e:
            print(f"Auto-panic error: {e}")
        await asyncio.sleep(5)
