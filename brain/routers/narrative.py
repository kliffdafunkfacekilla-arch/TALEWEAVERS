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
        # SagaGameLoop handles the directed graph workflow (Intent -> Lore -> Sim -> Narrative)
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
