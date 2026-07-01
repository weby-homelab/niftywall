from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import get_current_user, log_action
from app.db import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class TelegramSettingsRequest(BaseModel):
    bot_token: str = Field("", max_length=255)
    chat_id: str = Field("", max_length=255)


@router.get("/telegram")
async def get_telegram_settings(user: str = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'tg_bot_token'")
    token = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key = 'tg_chat_id'")
    chat_id = c.fetchone()
    conn.close()
    return {
        "bot_token": token[0] if token else "",
        "chat_id": chat_id[0] if chat_id else ""
    }


@router.post("/telegram")
async def update_telegram_settings(settings: TelegramSettingsRequest, user: str = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tg_bot_token', ?)", (settings.bot_token,))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tg_chat_id', ?)", (settings.chat_id,))
    conn.commit()
    conn.close()
    log_action(user, "UPDATE_SETTINGS", "Updated Telegram Alerts settings")
    return {"status": "success", "message": "Telegram settings updated successfully."}


@router.get("/audit")
async def get_audit_log(user: str = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT timestamp, username as user, action, details FROM audit_log ORDER BY id DESC LIMIT 100')
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []
