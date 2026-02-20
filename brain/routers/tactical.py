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
class TacticalFeedback(BaseModel):
    outcome: str
    enemies_killed: List[str]
    loot_taken: List[str]
    x: int
    y: int

class CombatActionRequest(BaseModel):
    action_type: str # 'skill', 'item', 'camp'
    target_id: Optional[str] = None
    item_id: Optional[str] = None
    skill_id: Optional[str] = None

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
def generate_tactical_map(x: Optional[int] = None, y: Optional[int] = None, poi_id: Optional[str] = None, db=Depends(get_db)):
    from combat.mechanics import CombatEngine
    width, height = 20, 20
    
    # 1. Resolve World Location
    if x is None or y is None:
        if db.campaign_gen and db.campaign_gen.current_campaign and db.campaign_gen.current_campaign.plot_points:
            x = db.campaign_gen.current_campaign.plot_points[0].x
            y = db.campaign_gen.current_campaign.plot_points[0].y
        else:
            x, y = 500, 500
            
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
                "icon": player_c.get_component(Renderable).icon if player_c.has_component(Renderable) else "sheet:115",
                "tags": ["hero"]
            })

    chest_loot = []
    if getattr(db, 'item_gen', None):
        chest_loot = [db.item_gen.generate_loot() for _ in range(2)]
        
    world_objects = [{"id": "chest_01", "name": "Ancient Chest", "type": "object", "pos": [width-3, 3], "icon": "sheet:6", "tags": ["lootable", "openable"], "inventory": chest_loot}]
    vtt_entities.extend(world_objects)

    # -------------------------------------------------------------
    # Inject Active Campaign POIs & Quest Targets
    # -------------------------------------------------------------
    if db.campaign_gen and db.campaign_gen.current_campaign:
        active_camp = db.campaign_gen.current_campaign
        for poi in active_camp.pois:
            if abs(poi.x - x) < 50 and abs(poi.y - y) < 50 and not poi.discovered:
                poi.discovered = True
                lx, ly = random.randint(2, width-3), random.randint(2, height-3)
                icon, poi_type, tags = "sheet:5074", "object", ["poi", "interactable"]
                
                if poi.type == "Person": icon, poi_type, tags = "sheet:3", "npc", ["poi", "interactable", "talkable"]
                elif poi.type == "Hostile Monster": 
                    if getattr(db, 'enemy_gen', None):
                        enemy = db.enemy_gen.generate_enemy(species_name="Gore-Beast", icon="sheet:5076")
                        enemy["id"] = poi.id
                        enemy["pos"] = [lx, ly]
                        enemy["tags"].extend(["poi", "interactable"])
                        enemy["description"] = poi.description
                        vtt_entities.append(enemy)
                        continue
                    else:
                        icon, poi_type, tags = "sheet:5076", "enemy", ["poi", "interactable", "hostile"]
                elif poi.type == "Corpse": icon, poi_type, tags = "sheet:14", "object", ["poi", "interactable", "searchable"]
                elif poi.type == "Item": icon, poi_type, tags = "sheet:6", "item", ["poi", "interactable", "lootable"]
                
                vtt_entities.append({
                    "id": poi.id, "name": f"{poi.type} (Quest Seed)", "type": poi_type,
                    "pos": [lx, ly], "icon": icon, "tags": tags, "description": poi.description
                })

    return {
        "meta": {"title": "Wilderness Encounter", "world_pos": [x, y], "description": "You scan the tactical area..."},
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

@router.post("/feedback")
def process_tactical_feedback(req: TacticalFeedback, db=Depends(get_db)):
    return {"status": "success", "message": f"Combat outcome: {req.outcome} recorded."}

@router.post("/travel")
def travel_to_node(db=Depends(get_db)):
    """Handles edge-of-map map transitioning. Advances time and moves to next POI."""
    new_x, new_y = 500, 500
    
    # 1. Advanced Time
    if getattr(db, 'sim', None):
        db.sim.advance_time(8, (new_x, new_y))
        
    # 2. Pick next target
    if db.campaign_gen and db.campaign_gen.current_campaign:
        # Find first undiscovered POI
        for poi in db.campaign_gen.current_campaign.pois:
            if not poi.discovered:
                new_x, new_y = poi.x, poi.y
                break
        else:
            # Or fall back to next plot point
            if len(db.campaign_gen.current_campaign.plot_points) > 1:
                new_x = db.campaign_gen.current_campaign.plot_points[1].x
                new_y = db.campaign_gen.current_campaign.plot_points[1].y
                
    # 3. Generate New Map
    return generate_tactical_map(x=new_x, y=new_y, db=db)

@router.post("/action")
def execute_system_action(req: CombatActionRequest, db=Depends(get_db)):
    """Executes a hard-coded system action, bypassing the LLM DM."""
    if not db.active_combat: raise HTTPException(status_code=400, detail="No active combat.")
    
    player_c = next((c for c in db.active_combat.combatants if "player" in c.name), None)
    if not player_c: raise HTTPException(status_code=400, detail="Player not found in combat.")
    
    updates = []
    log_msg = ""
    
    if req.action_type == "skill":
        target = next((c for c in db.active_combat.combatants if req.target_id and c.id == req.target_id), None)
        if target:
            logs = db.active_combat.attack_target(player_c, target, skill_used=req.skill_id)
            log_msg = f"You cast {req.skill_id}! " + " ".join(logs)
            updates.append({"type": "PLAY_ANIMATION", "name": "MAGIC", "target": target.id})
            updates.append({"type": "UPDATE_HP", "id": target.id, "hp": target.hp})
        else:
            log_msg = f"Target not valid for {req.skill_id}."
            
    elif req.action_type == "item":
        log_msg = f"You used {req.item_id}. Restored 20 HP!"
        player_c.hp = min(player_c.max_hp, player_c.hp + 20)
        updates.append({"type": "UPDATE_HP", "id": player_c.id, "hp": player_c.hp})
        
    elif req.action_type == "camp":
        log_msg = "You set up camp. 8 hours pass. Vitals restored."
        if db.sim: db.sim.advance_time(8, (player_c.x, player_c.y))
        player_c.hp = player_c.max_hp
        player_c.sp = player_c.max_sp
        updates.append({"type": "UPDATE_HP", "id": player_c.id, "hp": player_c.hp})
        
    return {
        "narrative": f"[SYSTEM] {log_msg}",
        "visual_updates": updates
    }
