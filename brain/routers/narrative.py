from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from brain.dependencies import get_db

router = APIRouter(prefix="/dm", tags=["narrative"])

# --- MODELS ---
class DMActionRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

# --- ENDPOINTS ---

@router.post("/action")
async def dm_action(req: DMActionRequest, db=Depends(get_db)):
    """
    Primary endpoint for the AI Dungeon Master. Orchestrates RAG context, 
    intent resolution, and narrative generation.
    """
    if not db.loop: raise HTTPException(status_code=503, detail="Game Loop Offline.")
    try:
        from core.ecs import world_ecs, Position
        player_data = req.context.get("player", {})
        player_pos = player_data.get("pos", [500, 500])
        
        nearby = []
        if db.active_combat:
            for c in db.active_combat.combatants:
                if c.id != player_data.get("id"):
                    nearby.append({"id": c.id, "name": c.name, "tags": list(c.tags) if hasattr(c, 'tags') else []})
        else:
            for e in world_ecs.entities.values():
                p = e.get_component(Position)
                if p and abs(p.x - player_pos[0]) < 20 and abs(p.y - player_pos[1]) < 20:
                    if e.id != player_data.get("id"):
                        nearby.append({"id": e.id, "name": e.name, "tags": list(e.tags) if hasattr(e, 'tags') else []})
                        
        req.context["environment"] = nearby
        return db.loop.process_turn(req.message, req.context)
    except Exception as e:
        print(f"[ERROR] Narrative Engine Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def narrative_health(db=Depends(get_db)):
    return {
        "status": "ready" if db.loop else "initializing",
        "rag_ready": db.rag is not None,
        "memory_size": len(db.memory.history) if db.memory else 0
    }

@router.get("/quests")
def get_active_quests(db=Depends(get_db)):
    """Returns active quests from the CampaignGenerator."""
    if db.campaign_gen and db.campaign_gen.current_campaign:
        active = []
        for pp in db.campaign_gen.current_campaign.plot_points:
            for q in pp.quests:
                if q.status == "active":
                    active.append({
                        "id": q.step_id,
                        "title": q.title,
                        "description": q.description,
                        "type": q.type,
                        "status": q.status
                    })
        return active
    return []
