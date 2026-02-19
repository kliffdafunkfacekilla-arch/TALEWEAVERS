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

# --- ENDPOINTS ---

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
