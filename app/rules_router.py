from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.auth import get_current_user, log_action
from app.nft_handler import NftablesHandler

router = APIRouter(prefix="/api/ruleset", tags=["ruleset"])


class PortRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("filter", pattern=r'^[\w\-]+$')
    chain: str = Field("input", pattern=r'^[\w\-]+$')
    port: int = Field(..., ge=1, le=65535)


class NATRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("niftywall", pattern=r'^[\w\-]+$')
    chain: str = Field("nw-prerouting", pattern=r'^[\w\-]+$')
    protocol: str = Field("tcp", pattern=r'^(tcp|udp)$')
    external_port: int = Field(..., ge=1, le=65535)
    internal_ip: str = Field(..., pattern=r'^[\w\.\:\-\/]+$')
    internal_port: Optional[int] = Field(None, ge=1, le=65535)


class SetElementRequest(BaseModel):
    family: str = Field(..., pattern=r'^(ip|ip6|inet)$')
    table: str = Field(..., pattern=r'^[\w\-]+$')
    set_name: str = Field(..., pattern=r'^[\w\-]+$')
    element: str = Field(..., pattern=r'^[\w\.\:\-\/]+$')


class AdvancedRuleRequest(BaseModel):
    family: str = Field("inet", pattern=r'^(ip|ip6|inet)$')
    table: str = Field("niftywall", pattern=r'^[\w\-]+$')
    chain: str = Field("nw-input", pattern=r'^[\w\-]+$')
    protocol: str = Field("tcp", pattern=r'^(tcp|udp)$')
    ports: str = Field("", pattern=r'^[\d\,]*$')
    source: str = Field("any", pattern=r'^[\w\.\:\-\/\@]+$')
    action: str = Field("accept", pattern=r'^(accept|drop)$')
    rate_enabled: bool = False
    rate: int = Field(0, ge=0)
    unit: str = Field("second", pattern=r'^(second|minute|hour|day)$')
    burst: int = Field(0, ge=0)


nft = NftablesHandler()


@router.get("")
async def get_ruleset(user: str = Depends(get_current_user)):
    try:
        data = nft.get_ruleset()
        if "error" in data:
            raise HTTPException(status_code=500, detail="Failed to fetch ruleset. Check system logs.")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/advanced")
async def add_advanced_rule(req: AdvancedRuleRequest, user: str = Depends(get_current_user)):
    try:
        res = nft.add_advanced_rule(
            family=req.family,
            table=req.table,
            chain=req.chain,
            protocol=req.protocol,
            ports=req.ports,
            source=req.source,
            action=req.action,
            rate_enabled=req.rate_enabled,
            rate=req.rate,
            unit=req.unit,
            burst=req.burst
        )
        if res["success"]:
            log_action(user, "ADD_RULE", f"New rule in {req.chain}")
            return {"status": "success", "message": "Rule applied successfully"}
        raise HTTPException(status_code=500, detail="Failed to apply advanced rule. Check system logs.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete("/{family}/{table}/{chain}/{handle}")
async def delete_rule(family: str, table: str, chain: str, handle: int, user: str = Depends(get_current_user)):
    success = nft.delete_rule(family, table, chain, handle)
    if success:
        log_action(user, "DELETE_RULE", f"Handle: {handle} from {chain}")
        return {"status": "success", "message": f"Rule {handle} deleted."}
    raise HTTPException(status_code=500, detail="Failed to delete rule.")


@router.post("/nat")
async def add_nat_rule(req: NATRequest, user: str = Depends(get_current_user)):
    res = nft.add_dnat_rule(
        req.family, req.table, req.chain, req.protocol,
        req.external_port, req.internal_ip, req.internal_port
    )
    if res["success"]:
        details = f"NAT: {req.protocol} {req.external_port} -> {req.internal_ip}:{req.internal_port or req.external_port}"
        log_action(user, "ADD_NAT", details)
        return {"status": "success", "message": "NAT Rule applied successfully."}
    raise HTTPException(status_code=500, detail="Failed to apply NAT rule. Check system logs.")


@router.post("/panic")
async def panic_mode(user: str = Depends(get_current_user)):
    success = nft.apply_panic_mode()
    if success:
        log_action(user, "PANIC_MODE", "Emergency lockdown activated")
        return {"status": "success", "message": "Panic mode activated!"}
    raise HTTPException(status_code=500, detail="Failed to activate panic mode.")


@router.post("/restore-panic")
async def restore_panic(user: str = Depends(get_current_user)):
    snapshots = nft.list_snapshots()
    if not snapshots:
        raise HTTPException(status_code=404, detail="No snapshots found to restore from.")
    latest = snapshots[0]['filename']
    success = nft.restore_snapshot(latest)
    if success:
        log_action(user, "EXIT_PANIC", f"Restored from {latest}")
        return {"status": "success", "message": "Successfully exited Panic Mode."}
    raise HTTPException(status_code=500, detail="Failed to restore snapshot.")


@router.get("/sets")
async def get_sets(user: str = Depends(get_current_user)):
    data = nft.get_sets()
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data


@router.post("/sets/element")
async def add_set_element(req: SetElementRequest, user: str = Depends(get_current_user)):
    success = nft.add_set_element(req.family, req.table, req.set_name, req.element)
    if success:
        log_action(user, "SET_ADD", f"Added {req.element} to {req.set_name}")
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to add element.")


@router.delete("/sets/element")
async def remove_set_element(req: SetElementRequest, user: str = Depends(get_current_user)):
    success = nft.delete_set_element(req.family, req.table, req.set_name, req.element)
    if success:
        log_action(user, "SET_REMOVE", f"Removed {req.element} from {req.set_name}")
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to remove element.")
