from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.auth import get_current_user, log_action
from app.nft_handler import NftablesHandler

router = APIRouter(prefix="/api", tags=["snapshots"])

nft = NftablesHandler()


@router.get("/snapshots")
async def get_snapshots(user: str = Depends(get_current_user)):
    return nft.list_snapshots()


@router.post("/snapshots/restore/{filename}")
async def restore_snapshot(filename: str, user: str = Depends(get_current_user)):
    if nft.restore_snapshot(filename):
        log_action(user, "RESTORE", f"Restored snapshot: {filename}")
        return {"status": "success", "message": f"Snapshot {filename} restored."}
    raise HTTPException(status_code=500, detail="Failed to restore snapshot.")


@router.post("/backup")
async def create_backup(user: str = Depends(get_current_user)):
    filename = nft._create_snapshot("manual_backup")
    if filename:
        log_action(user, "BACKUP", f"Manual backup created: {filename}")
        return {"status": "success", "message": f"Backup created: {filename}"}
    raise HTTPException(status_code=500, detail="Failed to create backup.")
