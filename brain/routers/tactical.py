import os
import json
import random
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from brain.dependencies import get_db, DATA_DIR
from core.ecs import world_ecs, Position, Renderable, Vitals, Stats

router = APIRouter(prefix="/tactical", tags=["tactical"])

# --- MODELS ---
class TacticalHealth(BaseModel):
    current: int
    max: int

class TacticalCoords(BaseModel):
    x: int
    y: int

class EnemyState(BaseModel):
    id: str
    name: str
    type: str
    health: TacticalHealth
    coordinates: TacticalCoords

class PlayerTacticalStats(BaseModel):
    name: str
    health: TacticalHealth
    stamina: TacticalHealth
    focus: TacticalHealth
    composure: TacticalHealth
    coordinates: TacticalCoords
    attributes: Dict[str, int]

class TacticalStateResponse(BaseModel):
    round: int = 1
    turn_order: List[str] = []
    active_combatant: Optional[str] = None
    player_stats: PlayerTacticalStats
    enemy_list: List[EnemyState]
    active_effects: List[Dict[str, Any]] = []

# --- ENDPOINTS ---

@router.get("/generate")
def generate_tactical_map(x: int, y: int, poi_id: Optional[str] = None, db=Depends(get_db)):
    from combat.mechanics import CombatEngine
    width, height = 20, 20
    grid = [[896 if (gx == 0 or gx == width-1 or gy == 0 or gy == height-1 or random.random() < 0.1) else 128 for gx in range(width)] for gy in range(height)]
    
    db.active_combat = CombatEngine(cols=width, rows=height)
    db.active_combat.walls = {(gx, gy) for gy in range(height) for gx in range(width) if grid[gy][gx] == 896}
    
    nearby = [e for e in world_ecs.entities.values() if e.has_component(Position)]
    vtt_entities = []
    for e in nearby:
        p = e.get_component(Position)
        vtt_entities.append({
            "id": e.id, "name": e.name,
            "type": 'enemy' if e.has_tag("faction") else 'object',
            "pos": [p.x, p.y],
            "hp": e.hp if e.has_component(Vitals) else None,
            "maxHp": e.max_hp if e.has_component(Vitals) else None,
            "icon": e.get_component(Renderable).icon if e.has_component(Renderable) else "sheet:5074",
            "tags": list(e.tags)
        })

    # Restore Player
    burt_path = os.path.join(DATA_DIR, "Saves", "Burt.json")
    if os.path.exists(burt_path):
        with open(burt_path, 'r', encoding='utf-8') as f:
            player_c = world_ecs.create_character(json.load(f))
            player_c.name = "player_burt"
            player_c.x, player_c.y = 5, 5
            db.active_combat.combatants.append(player_c)
            vtt_entities.append({
                "id": player_c.id, "name": "Burt", "type": 'player',
                "pos": [5, 5], "hp": player_c.hp, "maxHp": player_c.max_hp,
                "icon": player_c.get_component(Renderable).icon,
                "tags": ["hero"]
            })

    return {
        "meta": {"title": "Wilderness Encounter", "world_pos": [x, y]},
        "map": {"width": width, "height": height, "grid": grid, "biome": "forest"},
        "entities": vtt_entities,
        "log": ["Tactical simulation initiated."]
    }

@router.get("/state", response_model=TacticalStateResponse)
def get_tactical_state(db=Depends(get_db)):
    if not db.active_combat: raise HTTPException(status_code=404, detail="No active session.")
    player_c = next((c for c in db.active_combat.combatants if "player" in c.name), None)
    if not player_c: raise HTTPException(status_code=404, detail="Player not found.")
    
    return TacticalStateResponse(
        player_stats=PlayerTacticalStats(
            name=player_c.name,
            health=TacticalHealth(current=player_c.hp, max=player_c.max_hp),
            stamina=TacticalHealth(current=player_c.sp, max=player_c.max_sp),
            focus=TacticalHealth(current=player_c.fp, max=player_c.max_fp),
            composure=TacticalHealth(current=player_c.cmp, max=player_c.max_cmp),
            coordinates=TacticalCoords(x=player_c.x, y=player_c.y),
            attributes=player_c.get_component(Stats).attrs if player_c.has_component(Stats) else {}
        ),
        enemy_list=[
            EnemyState(
                id=c.id, name=c.name, type="Enemy",
                health=TacticalHealth(current=c.hp, max=c.max_hp),
                coordinates=TacticalCoords(x=c.x, y=c.y)
            ) for c in db.active_combat.combatants if "enemy" in c.name
        ]
    )

# --- CHARACTER ENDPOINT --- (Keeping near tactical)
@router.get("/char/{name}")
def get_character(name: str):
    player = next((e for e in world_ecs.entities.values() if e.name.lower() == name.lower()), None)
    if player: return player.to_dict()
    
    save_path = os.path.join(DATA_DIR, "Saves", f"{name}.json")
    if os.path.exists(save_path):
        with open(save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Character not found.")
