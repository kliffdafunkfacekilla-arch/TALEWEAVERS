import os
import json
import sqlite3
import uuid
import random
import subprocess
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from brain.dependencies import get_db, DATA_DIR, TALEWEAVERS_ROOT
from core.ecs import world_ecs
from core.models.definitions import SpeciesDefinition, FactionDefinition, WildlifeDefinition, FloraDefinition, ResourceDefinition

router = APIRouter(prefix="/architect", tags=["architect"])

# --- MODELS ---
class SimulationRequest(BaseModel):
    entities: List[Dict[str, Any]]
    years: int = 100

class PaintRequest(BaseModel):
    x: int
    y: int
    tile_index: int
    radius: int = 2

# 4-Layer Hierarchy Models
class GlobalRegionRequest(BaseModel):
    id: int
    name: str
    grid_x: int
    grid_y: int
    biome_data: Dict[str, Any]
    political_data: Dict[str, Any] = {}

class LocalZoneRequest(BaseModel):
    id: str
    global_region_id: int
    region_x: int
    region_y: int
    terrain_data: Dict[str, Any]

class PlayerMapRequest(BaseModel):
    id: str
    local_zone_id: str
    local_x: int
    local_y: int
    map_data: Dict[str, Any]

# --- ENDPOINTS ---

# ... [Existing Endpoints] ...

@router.post("/simulate")
async def run_world_simulation(req: SimulationRequest, db=Depends(get_db)):
    """
    Invokes the C++ Headless Engine to generate history based on the editor's seed state.
    """
    print(f"[ARCHITECT] Initializing Simulation Bridge for {req.years} years...")
    
    seed_path = os.path.join(DATA_DIR, "seed_state.json")
    with open(seed_path, 'w', encoding='utf-8') as f:
        json.dump({"agents": req.entities}, f, indent=4)
    
    engine_path = os.path.join(TALEWEAVERS_ROOT, "FantasyLloreAndWorldSimulator", "bin", "TALEWEAVERS_Engine.exe")
    if not os.path.exists(engine_path):
        engine_path = os.path.join(TALEWEAVERS_ROOT, "bin", "TALEWEAVERS_Engine.exe")

    if not os.path.exists(engine_path):
        raise HTTPException(status_code=500, detail="Simulation Engine executable missing.")

    try:
        proc = subprocess.run([engine_path, str(req.years)], capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Engine error: {proc.stderr}")
            
        # ETL Bridge: Import Simulation Results
        from core.import_world import WorldImporter
        importer = WorldImporter()
        importer.clear_world()
        
        master_export = os.path.join(DATA_DIR, "master_export.json")
        importer.import_entities(master_export)
        world_ecs.load_all() # Refresh registry
        
        # Local Layer Simulation (Python Side)
        from core.systems.settlement import SettlementSystem
        settlement_sim = SettlementSystem(world_ecs, db.definitions)
        for _ in range(req.years):
            settlement_sim.process_tick()
            
        # Optional: Save back the updated state after python sim
        for entity in world_ecs.entities.values():
            world_ecs.db.save_entity(entity.id, entity.name, entity.to_dict())
        
        return {"status": "success", "log": proc.stdout.splitlines()[-5:], "years_simulated": req.years}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/list")
async def list_world_history():
    history_dir = os.path.join(DATA_DIR, "history")
    if not os.path.exists(history_dir): return {"years": []}
    
    files = os.listdir(history_dir)
    years = []
    for f in files:
        if f.startswith("year_") and f.endswith(".map"):
            try: years.append(int(f.replace("year_", "").replace(".map", "")))
            except: continue
    return {"years": sorted(years)}

@router.post("/history/load/{year}")
async def load_historical_year(year: int):
    snapshot_path = os.path.join(DATA_DIR, "history", f"year_{year}.map")
    if not os.path.exists(snapshot_path):
        raise HTTPException(status_code=404, detail="Snapshot not found.")

    engine_path = os.path.join(TALEWEAVERS_ROOT, "FantasyLloreAndWorldSimulator", "bin", "TALEWEAVERS_Engine.exe")
    if not os.path.exists(engine_path):
        engine_path = os.path.join(TALEWEAVERS_ROOT, "bin", "TALEWEAVERS_Engine.exe")

    try:
        subprocess.run([engine_path, "--export", snapshot_path], capture_output=True, text=True, timeout=30)
        from core.import_world import WorldImporter
        importer = WorldImporter()
        importer.clear_world()
        importer.import_entities(os.path.join(DATA_DIR, "master_export.json"))
        world_ecs.load_all()
        return {"status": "success", "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grid")
def get_architect_grid(db=Depends(get_db)):
    if not db.world_grid: raise HTTPException(status_code=503, detail="Grid Offline.")
    return {"width": db.world_grid.width, "height": db.world_grid.height, "grid": db.world_grid.grid}

@router.post("/paint")
def paint_architect_grid(req: PaintRequest, db=Depends(get_db)):
    if not db.world_grid: raise HTTPException(status_code=503, detail="Grid Offline.")
    db.world_grid.paint(req.x, req.y, req.tile_index, req.radius)
    db.world_grid.save()
    return {"status": "success"}

@router.post("/sync/vault")
async def sync_vault(db=Depends(get_db)):
    from tools.vault_compiler import VaultCompiler, VAULT_PATH, DB_PATH
    from core.rag import SimpleRAG
    try:
        compiler = VaultCompiler(VAULT_PATH, DB_PATH)
        compiler.compile()
        compiler.auto_populate()
        
        world_ecs.load_all()
        if db.rag: # Re-init RAG to pick up new lore
            db.rag = SimpleRAG(data_path=os.path.join(DATA_DIR, "lore"), async_init=False)
            
        return {"status": "success", "message": "Vault synced and seeded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4-Layer Hierarchy Endpoints ---

@router.get("/regions")
def get_global_regions(db=Depends(get_db)):
    return db.db.get_global_regions()

@router.post("/region")
def create_global_region(req: GlobalRegionRequest, db=Depends(get_db)):
    db.db.create_global_region(req.id, req.name, req.grid_x, req.grid_y, req.biome_data, req.political_data)
    return {"status": "success"}

@router.get("/region/{region_id}/zones")
def get_local_zones(region_id: int, db=Depends(get_db)):
    return db.db.get_local_zones(region_id)

@router.post("/zone")
def create_local_zone(req: LocalZoneRequest, db=Depends(get_db)):
    db.db.create_local_zone(req.id, req.global_region_id, req.region_x, req.region_y, req.terrain_data)
    return {"status": "success"}

@router.get("/map/{map_id}")
def get_player_map(map_id: str, db=Depends(get_db)):
    m = db.db.get_player_map(map_id)
    if not m: raise HTTPException(status_code=404, detail="Map not found")
    return m

@router.post("/map")
def create_player_map(req: PlayerMapRequest, db=Depends(get_db)):
    db.db.create_player_map(req.id, req.local_zone_id, req.local_x, req.local_y, req.map_data)
    return {"status": "success"}

@router.post("/advance_time")
def advance_world_time(hours: int = Query(1), x: int = Query(500), y: int = Query(500), db=Depends(get_db)):
    """
    Advances world time and triggers hierarchical simulation ticks (LOD-aware).
    """
    if not db.sim:
        raise HTTPException(status_code=503, detail="Simulation Engine Offline.")
    
    db.sim.advance_time(hours, player_pos=(x, y))
    
    # Save updated gamestate
    try:
        from brain.dependencies import GAMESTATE_PATH
        with open(GAMESTATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(db.gamestate, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save updated gamestate: {e}")

    return {
        "status": "Time Advanced",
        "new_time": db.sim.get_time_string(),
        "epoch": db.gamestate.get('meta', {}).get('epoch', 0),
        "global_wealth": db.gamestate.get('meta', {}).get('global_wealth', 0)
    }

# --- Phase 7 Asset Endpoints ---
@router.get("/assets")
async def get_all_assets(db=Depends(get_db)):
    """Returns all loaded JSON definition assets for the VTT Editor."""
    return {
        "species": [s.model_dump() for s in db.definitions.species.values()],
        "factions": [f.model_dump() for f in db.definitions.factions.values()],
        "resources": [r.model_dump() for r in db.definitions.resources.values()],
        "wildlife": [w.model_dump() for w in db.definitions.wildlife.values()],
        "flora": [fl.model_dump() for fl in db.definitions.flora.values()]
    }

class AssetUpdatePayload(BaseModel):
    category: str
    data: Dict[str, Any]

@router.post("/assets")
async def save_asset(payload: AssetUpdatePayload, db=Depends(get_db)):
    """Saves a modified asset definition back to disk."""
    cat = payload.category
    data = payload.data
    
    try:
        if cat == "species":
            obj = SpeciesDefinition(**data)
            db.definitions.species[obj.id] = obj
        elif cat == "factions":
            obj = FactionDefinition(**data)
            db.definitions.factions[obj.id] = obj
        elif cat == "resources":
            obj = ResourceDefinition(**data)
            db.definitions.resources[obj.id] = obj
        elif cat == "wildlife":
            obj = WildlifeDefinition(**data)
            db.definitions.wildlife[obj.id] = obj
        elif cat == "flora":
            obj = FloraDefinition(**data)
            db.definitions.flora[obj.id] = obj
        else:
            raise HTTPException(status_code=400, detail="Invalid asset category")
            
        db.definitions.save_definition(cat, obj)
        return {"status": "success", "message": f"Saved {cat} asset: {obj.id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
