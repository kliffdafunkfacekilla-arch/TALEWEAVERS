import os
import json
import random
import datetime
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
    skill_name: Optional[str] = None

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
    # Inject test spells & skills for Phase 47/48
    if "Spells" not in char_data:
        char_data["Spells"] = ["Push", "Flame Spit", "Shocking Burst"] 
    if "Skills" not in char_data:
        char_data["Skills"] = ["BREAKER (Siegecraft)", "SPRINTER (Evasion)", "INTIMIDATOR (Presence)"]
        
    char_entity = world_ecs.create_character(char_data)
    char_entity.add_tag("hero")
    char_entity.x, char_entity.y = 2, 2
    db.active_combat.combatants.append(char_entity)
    
    # Add Hazards
    db.active_combat.terrain[(4, 4)] = "ACID"
    db.active_combat.terrain[(5, 4)] = "ACID"
    db.active_combat.terrain[(6, 6)] = "LAVA"
    db.active_combat.terrain[(5, 6)] = "POISON"
    
    # Add Bushes (Difficult Terrain)
    db.active_combat.terrain[(4, 2)] = "DIFFICULT"
    db.active_combat.terrain[(4, 3)] = "DIFFICULT"
    db.active_combat.terrain[(6, 2)] = "DIFFICULT"
    db.active_combat.terrain[(6, 6)] = "LAVA"
    db.active_combat.terrain[(6, 7)] = "GOO" # Near lava
    db.active_combat.terrain[(5, 5)] = "STEAM_VENT"
    db.active_combat.terrain[(4, 4)] = "STEAM_VENT"
    db.active_combat.terrain[(4, 3)] = "ACID"
    db.active_combat.terrain[(5, 3)] = "WOODEN_BRIDGE" # Link over acid
    db.active_combat.terrain[(3, 3)] = "WOODEN_BRIDGE" # Link over acid
    
    # Add Environmental Triggers
    db.active_combat.terrain[(2, 2)] = "ACID_BARREL"
    
    # Update visual grid cells for hazards and triggers
    if db.active_combat.grid_cells:
        db.active_combat.grid_cells[4][4] = 131 # Acid
        db.active_combat.grid_cells[2][2] = 133 # Example Barrel Sprite
        db.active_combat.grid_cells[6][6] = 132 # Lava
    # Spawn a Predator Pack
    # 1. Predator Alpha (Tanky, Leads the pack)
    alpha = world_ecs.create_character({
        "Name": "Predator Alpha",
        "Stats": {"Vitality": 20, "Fortitude": 12, "Endurance": 15, "Might": 14, "Reflexes": 8},
        "Team": "Enemy",
        "Traits": {
            "Pack Tactics": "Gains bonus to hit when allies are nearby.",
            "Adaptive Carapace": "Hardens against the last damage type taken."
        },
        "Evolution Traits": {
            "HEAD": {"mental": "Logic", "physical": "Might"} # Might Nose: Heavy-Scent
        },
        "Spells": ["Shocking Burst"],
        "Skills": ["BREAKER (Siegecraft)"]
    })
    alpha.x, alpha.y = 8, 8
    db.active_combat.combatants.append(alpha)

    # 2. Stalker A (Fast, flanking)
    stalker_a = world_ecs.create_character({
        "Name": "Iron-Tail Stalker A",
        "Stats": {"Vitality": 10, "Reflexes": 14, "Endurance": 12, "Might": 10},
        "Team": "Enemy",
        "Traits": {"Pack Tactics": "Coordination bonus."}
    })
    stalker_a.get_component(Renderable).icon = "sheet:5076"
    stalker_a.x, stalker_a.y = 7, 9
    db.active_combat.combatants.append(stalker_a)

    # 3. Stalker B (Fast, flanking)
    stalker_b = world_ecs.create_character({
        "Name": "Iron-Tail Stalker B",
        "Stats": {"Vitality": 10, "Reflexes": 14, "Endurance": 12, "Might": 10},
        "Team": "Enemy",
        "Traits": {"Pack Tactics": "Coordination bonus."}
    })
    stalker_b.get_component(Renderable).icon = "sheet:5076"
    stalker_b.x, stalker_b.y = 9, 7
    db.active_combat.combatants.append(stalker_b)

    # 4. Long-Range Spitter (Sniper)
    spitter = world_ecs.create_character({
        "Name": "Long-Range Spitter",
        "Stats": {"Vitality": 12, "Reflexes": 15, "Endurance": 10},
        "Team": "Enemy",
        "Archetype": "SNIPER",
        "Skills": ["MARKSMAN (Ballistics)"]
    })
    spitter.get_component(Renderable).icon = "sheet:5077"
    spitter.x, spitter.y = 2, 7 # On the central peak of the plateau
    db.active_combat.combatants.append(spitter)

    # 5. Swarm Herald (Healer)
    herald = world_ecs.create_character({
        "Name": "Swarm Herald",
        "Stats": {"Vitality": 15, "Reflexes": 10, "Endurance": 12},
        "Team": "Enemy",
        "Archetype": "HEALER",
        "Skills": ["MEDIC (First Aid)"]
    })
    herald.get_component(Renderable).icon = "sheet:5079"
    herald.x, herald.y = 9, 9 # Back corner
    db.active_combat.combatants.append(herald)

    # 6. Ledge Victim (For Shove Testing)
    victim = world_ecs.create_character({
        "Name": "Ledge Stalker",
        "Stats": {"Vitality": 10, "Reflexes": 12, "Endurance": 10},
        "Team": "Enemy",
        "Archetype": "MELEE"
    })
    victim.get_component(Renderable).icon = "sheet:5076"
    victim.x, victim.y = 3, 6 # Edge of the plateau
    db.active_combat.combatants.append(victim)

    # 7. Pheromone Herald (Pack Buffer)
    herald_p = world_ecs.create_character({
        "Name": "Pheromone Herald",
        "Stats": {"Vitality": 15, "Reflexes": 10, "Endurance": 12, "Might": 8},
        "Team": "Enemy",
        "Traits": {
            "Pheromone Synthesis": "Buffs nearby allies with biological scents.",
            "Adaptive Carapace": "Hardens against damage."
        }
    })
    herald_p.get_component(Renderable).icon = "sheet:5076"
    herald_p.x, herald_p.y = 7, 7 # Center of the enemy pack
    db.active_combat.combatants.append(herald_p)

    # 8. Symbiotic Pair
    bonded_a = world_ecs.create_character({
        "Name": "Bonded Hunter A",
        "Stats": {"Vitality": 15, "Reflexes": 10}, "Team": "Enemy",
        "Traits": {"Symbiotic": "Shares life force with its partner."}
    })
    bonded_a.x, bonded_a.y = 5, 5
    
    bonded_b = world_ecs.create_character({
        "Name": "Bonded Hunter B",
        "Stats": {"Vitality": 15, "Reflexes": 10}, "Team": "Enemy",
        "Traits": {"Symbiotic": "Shares life force with its partner."}
    })
    bonded_b.x, bonded_b.y = 5, 4
    
    # Establish Link
    bonded_a.symbiotic_link = bonded_b.id
    bonded_b.symbiotic_link = bonded_a.id
    
    db.active_combat.combatants.append(bonded_a)
    db.active_combat.combatants.append(bonded_b)

    # 9. THE EVOLUTIONARY OVERLORD (Boss)
    overlord = world_ecs.create_character({
        "Name": "Evolutionary Overlord",
        "Stats": {"Vitality": 100, "Reflexes": 15, "Might": 20, "Endurance": 20},
        "Team": "Enemy",
        "Traits": {
            "Pheromone Synthesis": "Buffs large radius.",
            "Adaptive Carapace": "Hardens on hit.",
            "Primal Fury": "Enrages at low HP."
        },
        "Evolution Traits": {
            "BODY": {"mental": "Willpower", "physical": "Fortitude"}, # Willpower Resistant: Inertia
            "ARMS": {"mental": "Might", "physical": "Willpower"} # Might Steadfast: Titan-Grip
        }
    })
    overlord.tags.add("boss")
    overlord.get_component(Renderable).icon = "sheet:5078"
    overlord.x, overlord.y = 9, 5 # Boss Arena Position
    
    # Boss Guardians (Symbiotic Links)
    gb1 = world_ecs.create_character({"Name": "Overlord Guardian A", "Stats": {"Vitality": 30, "Reflexes": 10}, "Team": "Enemy"})
    gb1.x, gb1.y = 8, 4
    gb1.symbiotic_link = overlord.id
    
    gb2 = world_ecs.create_character({"Name": "Overlord Guardian B", "Stats": {"Vitality": 30, "Reflexes": 10}, "Team": "Enemy"})
    gb2.x, gb2.y = 8, 6
    gb2.symbiotic_link = overlord.id
    
    # Note: Currently splitting logic only allows 1 link, but we'll link Boss to A for now
    overlord.symbiotic_link = gb1.id 
    
    db.active_combat.combatants.append(overlord)
    db.active_combat.combatants.append(gb1)
    db.active_combat.combatants.append(gb2)

    # Seed Items
    db.active_combat.items[(3, 1)] = "MIGHT_VIAL"
    db.active_combat.items[(1, 4)] = "SPEED_VIAL"
    db.active_combat.items[(5, 2)] = "BIOMASS"

    # Seed Elevation
    for x in range(1, 4):
        for y in range(6, 9):
            db.active_combat.elevation[(x, y)] = 1 # A small plateau
    db.active_combat.elevation[(2, 7)] = 2 # A high peak
    
    return {
        "status": "success",
        "character": char_entity.to_dict(),
        "grid": {
            "cols": 10, 
            "rows": 10, 
            "cells": grid,
            "terrain": {f"{x},{y}": t for (x, y), t in db.active_combat.terrain.items()},
            "items": {f"{x},{y}": i for (x, y), i in db.active_combat.items.items()},
            "elevation": {f"{x},{y}": h for (x, y), h in db.active_combat.elevation.items()},
            "threat": db.active_combat.threat
        }
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
            "tags": list(c.tags),
            "statusEffects": getattr(c, "status_effects", []),
            "tempBuffs": getattr(c, "temp_buffs", []),
            "symbioticLink": getattr(c, "symbiotic_link", None),
            "metadata": c.metadata
        })
        
    return {
        "status": "active",
        "entities": entities,
        "grid": {
            "cols": db.active_combat.cols,
            "rows": db.active_combat.rows,
            "cells": db.active_combat.grid_cells,
            "terrain": {f"{x},{y}": t for (x, y), t in db.active_combat.terrain.items()},
            "items": {f"{x},{y}": i for (x, y), i in db.active_combat.items.items()},
            "elevation": {f"{x},{y}": h for (x, y), h in db.active_combat.elevation.items()},
            "threat": db.active_combat.threat
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
        "parameters": {"dx": req.dx, "dy": req.dy, "x": req.x, "y": req.y, "skill_name": req.skill_name}
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

@router.post("/export_combat")
def export_combat(db=Depends(get_db)):
    if not db.active_combat:
        raise HTTPException(status_code=400, detail="No active combat.")
    
    # Package Data
    export_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "round_count": db.active_combat.round_count,
        "survivors": [{"id": c.id, "name": c.name, "hp": c.hp, "maxHp": getattr(c, "max_hp", 0)} for c in db.active_combat.combatants if c.hp > 0],
        "casualties": [{"id": c.id, "name": c.name} for c in db.active_combat.combatants if c.hp <= 0],
        "final_terrain": {f"{x},{y}": t for (x, y), t in db.active_combat.terrain.items()},
        "replay_log": db.active_combat.replay_log
    }

    # Save to Atomic Lore Piece directory
    lore_dir = os.path.join(DATA_DIR, "lore", "history")
    os.makedirs(lore_dir, exist_ok=True)
    filename = f"combat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(lore_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=4)
        
    db.active_combat = None # Clear active combat
    
    return {"status": "success", "file": filename, "message": "Combat exported to Lore History."}


