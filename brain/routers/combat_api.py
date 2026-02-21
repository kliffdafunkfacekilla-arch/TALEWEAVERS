import os
import json
import random
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from brain.dependencies import get_db, DATA_DIR
from core.ecs import world_ecs, Position, Vitals, Stats, Renderable
from core.combat.mechanics import CombatEngine

router = APIRouter(prefix="/combat", tags=["combat"])

class CombatLoadRequest(BaseModel):
    character_name: str

class CombatActionRequest(BaseModel):
    action: str # MOVE, ATTACK
    target_id: Optional[str] = None
    dx: Optional[int] = 0
    dy: Optional[int] = 0
    x: Optional[int] = 0
    y: Optional[int] = 0

@router.get("/saves")
def list_saves():
    saves_dir = os.path.join(DATA_DIR, "Saves")
    if not os.path.exists(saves_dir): return []
    return [f.replace(".json", "") for f in os.listdir(saves_dir) if f.endswith(".json")]

@router.post("/load")
def load_character(req: CombatLoadRequest, db=Depends(get_db)):
    save_path = os.path.join(DATA_DIR, "Saves", f"{req.character_name}.json")
    if not os.path.exists(save_path):
        raise HTTPException(status_code=404, detail="Character not found.")
    
    with open(save_path, 'r', encoding='utf-8') as f:
        char_data = json.load(f)
    
    # Initialize 10x10 grid with obstacles for Battle Lab
    width, height = 10, 10
    grid = [[128 for _ in range(width)] for _ in range(height)]
    walls = set()
    terrain = {} # (x, y) -> terrain_type
    
    # Random seeding
    for _ in range(12): # 12 obstacles
        rx, ry = random.randint(0, 9), random.randint(0, 9)
        if (rx, ry) in [(2, 2), (7, 7)]: continue # Don't block start/dummy
        
        otype = random.choice(["WALL", "BUSH"])
        if otype == "WALL":
            grid[ry][rx] = 896
            walls.add((rx, ry))
        else:
            grid[ry][rx] = 130
            terrain[(rx, ry)] = "DIFFICULT"
            
    db.active_combat = CombatEngine(cols=width, rows=height)
    db.active_combat.walls = walls
    db.active_combat.terrain = terrain
    db.active_combat.grid_cells = grid # Store the visual grid reference
    
    # Create ECS Entity
    char_entity = world_ecs.create_character(char_data)
    char_entity.add_tag("hero")
    char_entity.x, char_entity.y = 2, 2
    db.active_combat.combatants.append(char_entity)
    
    # Add a Target Dummy
    dummy = world_ecs.create_character({
        "Name": "Target Dummy",
        "Stats": {"Vitality": 10, "Fortitude": 10, "Endurance": 10, "Reflexes": 5},
        "Team": "Enemy"
    })
    dummy.x, dummy.y = 7, 7
    db.active_combat.combatants.append(dummy)
    
    return {
        "status": "success",
        "character": char_entity.to_dict(),
        "grid": {"cols": 10, "rows": 10, "cells": grid}
    }

@router.get("/state")
def get_combat_state(db=Depends(get_db)):
    if not db.active_combat:
        return {"status": "inactive"}
    
    entities = []
    for c in db.active_combat.combatants:
        entities.append({
            "id": c.id,
            "name": c.name,
            "pos": [c.x, c.y],
            "hp": c.hp,
            "maxHp": c.max_hp,
            "sp": c.sp,
            "maxSp": c.max_sp,
            "fp": c.fp,
            "maxFp": c.max_fp,
            "cmp": c.cmp,
            "maxCmp": c.max_cmp,
            "icon": c.get_component(Renderable).icon if c.has_component(Renderable) else "sheet:5074",
            "tags": list(c.tags)
        })
        
    return {
        "status": "active",
        "entities": entities,
        "grid": {
            "cols": db.active_combat.cols,
            "rows": db.active_combat.rows,
            "cells": db.active_combat.grid_cells
        },
        "round": db.active_combat.round_count,
        "log": db.active_combat.replay_log
    }

@router.post("/action")
def execute_combat_action(req: CombatActionRequest, db=Depends(get_db)):
    if not db.active_combat:
        raise HTTPException(status_code=400, detail="No active combat.")
    
    player = next((c for c in db.active_combat.combatants if "hero" in c.tags), None)
    if not player:
        raise HTTPException(status_code=400, detail="Player not found.")
    
    intent = {
        "action": req.action,
        "target": req.target_id,
        "parameters": {"dx": req.dx, "dy": req.dy, "x": req.x, "y": req.y}
    }
    
    narrative, updates = db.active_combat.process_intent(intent)
    db.active_combat.replay_log.append(narrative)
    
    return {
        "status": "success",
        "narrative": narrative,
        "updates": updates
    }

@router.post("/end_turn")
def end_turn(db=Depends(get_db)):
    if not db.active_combat:
        raise HTTPException(status_code=400, detail="No active combat.")
    
    # 1. AI Actions
    db.active_combat.run_ai_turn()
    updates = db.active_combat.pending_updates
    
    # 2. End Round (Regen, etc)
    db.active_combat.end_round()
    
    return {"status": "success", "round": db.active_combat.round_count, "updates": updates}


