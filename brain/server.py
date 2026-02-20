import os
import json
import uvicorn
import math
import random
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

# --- CONFIGURATION ---
BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
TALEWEAVERS_ROOT = os.path.dirname(BRAIN_DIR)
DATA_DIR = os.path.join(TALEWEAVERS_ROOT, "data")
CORE_DIR = os.path.join(TALEWEAVERS_ROOT, "core")

# Bring in Core Rules Engine
if TALEWEAVERS_ROOT not in sys.path:
    sys.path.append(TALEWEAVERS_ROOT)
if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)
if BRAIN_DIR not in sys.path:
    sys.path.append(BRAIN_DIR)

try:
    from campaign_system import CampaignGenerator, POIType, QuestType, CampaignState
    from combat.mechanics import CombatEngine
    from core.sensory_layer import SensoryLayer
    from core.item_generator import ItemGenerator
    from core.quest_manager import QuestManager
    from world.sim_manager import SimulationManager
    from core.memory import MemoryManager
    from world.graph_manager import WorldGraph
    from core.database import PersistenceLayer
    from core.rag import SimpleRAG
    from workflow.gamestate_machine import SagaGameLoop
    from core.ecs import world_ecs, Renderable, Vitals, Stats, Position, FactionMember
    from core.world_grid import WorldGrid
except ImportError as e:
    print(f"[ERROR] Failed to import internal Core components: {e}")
    CampaignGenerator = None
    CombatEngine = None
    SensoryLayer = None
    ItemGenerator = None
    QuestManager = None
    PersistenceLayer = None
    MemoryManager = None
    WorldGraph = None
    SimpleRAG = None
    SagaGameLoop = None
    SimulationManager = None
    WorldGrid = None

LORE_PATH = os.path.join(DATA_DIR, "lore.json")
GAMESTATE_PATH = os.path.join(DATA_DIR, "gamestate.json")

print(f"[BOOT] Taleweavers Brain initializing...")
print(f"[BOOT] Root: {TALEWEAVERS_ROOT}")
print(f"[BOOT] Data: {DATA_DIR}")

# --- DATA LOADER ---
class WorldDatabase:
    def __init__(self):
        self.lore = []
        self.gamestate = {}
        self.factions = {}
        self.nodes = []
        self.campaign_gen = CampaignGenerator(save_dir=os.path.join(DATA_DIR, "Saves")) if CampaignGenerator else None
        self.sensory = SensoryLayer(model="qwen2.5:latest") if SensoryLayer else None
        self.item_gen = ItemGenerator(os.path.join(DATA_DIR, "Item_Builder.json")) if ItemGenerator else None
        self.quests = QuestManager(os.path.join(DATA_DIR, "quests.json")) if QuestManager else None
        self.active_combat = None
        self.sim = None
        self.memory = None
        self.graph = None
        self.db = PersistenceLayer(os.path.join(DATA_DIR, "world_state.db")) if PersistenceLayer else None
        self.world_grid = WorldGrid(width=100, height=100, save_path=os.path.join(DATA_DIR, "world_grid.json")) if WorldGrid else None
        self.rag = None
        self.loop = None
    
    def load(self):
        # 1. Initialize RAG with Atomic Lore Directory (v2.0)
        lore_dir = os.path.join(DATA_DIR, "lore")
        if os.path.exists(lore_dir) and SimpleRAG:
            print(f"[BOOT] Building RAG index from atomic directory: {lore_dir}")
            self.rag = SimpleRAG(data_path=lore_dir, async_init=True)
        elif os.path.exists(LORE_PATH) and SimpleRAG:
            # Fallback to legacy lore.json
            print(f"[BOOT] WARNING: Using legacy lore.json. Atomic directory not found.")
            with open(LORE_PATH, 'r', encoding='utf-8') as f:
                self.lore = json.load(f)
            self.rag = SimpleRAG(lore_data=self.lore, async_init=True)

        try:
            if os.path.exists(GAMESTATE_PATH):
                with open(GAMESTATE_PATH, 'r', encoding='utf-8') as f:
                    self.gamestate = json.load(f)
                
                self.factions = {f['id']: f for f in self.gamestate.get('factions', [])}
                self.nodes = self.gamestate.get('nodes', [])
            
            if self.quests: self.quests.load()
            if SimulationManager: self.sim = SimulationManager(self.gamestate)
            if MemoryManager and self.sensory: self.memory = MemoryManager(self.sensory)
            if WorldGraph: self.graph = WorldGraph(self.nodes)
            if self.db: self.db.sync_nodes(self.nodes)

            if SagaGameLoop and self.sensory:
                self.loop = SagaGameLoop(
                    self.sensory, 
                    lambda: self.active_combat,
                    self.rag, 
                    self.memory,
                    self.sim,
                    self.quests,
                    self.campaign_gen
                )

            # --- RESTORE WORLD STATE ---
            world_ecs.load_all()
            
        except Exception as e:
            print(f"[ERROR] Failed to load gamestate/init components: {e}")

db = WorldDatabase()
db.load()

# --- APP SETUP ---
app = FastAPI(title="SAYA: SAGA Brain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class DMActionRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

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
    active_effects: List[Dict[str, Any]] = []

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
    active_effects: List[Dict[str, Any]]

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "online", "lore_count": len(db.lore)}

@app.post("/dm/action")
async def dm_action(req: DMActionRequest):
    if not db.loop: raise HTTPException(status_code=503, detail="Game Loop Offline.")
    try:
        # Augment context with environment details (nearby interactive objects)
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tactical/generate")
def generate_tactical_map(x: int, y: int, poi_id: Optional[str] = None):
    width, height = 20, 20
    grid = [[896 if (gx == 0 or gx == width-1 or gy == 0 or gy == height-1 or random.random() < 0.1) else 128 for gx in range(width)] for gy in range(height)]
    
    if CombatEngine:
        db.active_combat = CombatEngine(cols=width, rows=height)
        db.active_combat.walls = {(gx, gy) for gy in range(height) for gx in range(width) if grid[gy][gx] == 896}
        
        # Load Persistent Entities from the World Database
        # Filter for anything at these coordinates (approx)
        nearby = [e for e in world_ecs.entities.values() if e.has_component(Position)]
        
        vtt_entities = []
        for e in nearby:
            p = e.get_component(Position)
            # For now, let's just include all persistent entities that aren't the player
            # so the user can see them on the map.
            vtt_entities.append({
                "id": e.id,
                "name": e.name,
                "type": 'enemy' if e.has_tag("faction") else 'object',
                "pos": [p.x, p.y],
                "hp": e.hp if e.has_component(Vitals) else None,
                "maxHp": e.max_hp if e.has_component(Vitals) else None,
                "icon": e.get_component(Renderable).icon if e.has_component(Renderable) else "sheet:5074",
                "tags": list(e.tags)
            })

        # Load Player (Persistent Save)
        burt_path = os.path.join(DATA_DIR, "Saves", "Burt.json")
        if os.path.exists(burt_path):
            with open(burt_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
                player_c = world_ecs.create_character(char_data)
                player_c.name = "player_burt"
                player_c.x, player_c.y = 5, 5
                db.active_combat.combatants.append(player_c)
                vtt_entities.append({
                    "id": player_c.id,
                    "name": "Burt",
                    "type": 'player',
                    "pos": [5, 5],
                    "hp": player_c.hp, "maxHp": player_c.max_hp,
                    "icon": player_c.get_component(Renderable).icon if player_c.has_component(Renderable) else "sheet:115",
                    "tags": ["hero"]
                })

    world_objects = [{"id": "chest_01", "name": "Ancient Chest", "type": "object", "pos": [width-3, 3], "icon": "sheet:6", "tags": ["lootable", "openable"]}]
    vtt_entities.extend(world_objects)

    # -------------------------------------------------------------
    # Inject Active Campaign POIs & Quest Targets
    # -------------------------------------------------------------
    if db.campaign_gen and db.campaign_gen.current_campaign:
        active_camp = db.campaign_gen.current_campaign
        # Find POIs near this world_pos
        for poi in active_camp.pois:
            # If POI is within 50 units on the world map
            if abs(poi.x - x) < 50 and abs(poi.y - y) < 50 and not poi.discovered:
                poi.discovered = True
                
                # Pick a random local coordinate inside the 20x20 tactical map
                lx, ly = random.randint(2, width-3), random.randint(2, height-3)
                
                # Map POIType to VTT icons
                icon = "sheet:5074"
                poi_type = "object"
                tags = ["poi", "interactable"]
                
                if poi.type == "Person":
                    icon = "sheet:3"
                    poi_type = "npc"
                    tags.append("talkable")
                elif poi.type == "Hostile Monster":
                    icon = "sheet:5076"
                    poi_type = "enemy"
                    tags.append("hostile")
                elif poi.type == "Corpse":
                    icon = "sheet:14"
                    tags.append("searchable")
                elif poi.type == "Item":
                    icon = "sheet:6"
                    tags.append("lootable")
                
                vtt_entities.append({
                    "id": poi.id,
                    "name": f"{poi.type} (Quest Seed)",
                    "type": poi_type,
                    "pos": [lx, ly],
                    "icon": icon,
                    "tags": tags,
                    "description": poi.description
                })

    return {
        "meta": {"title": "Wilderness Encounter", "world_pos": [x, y], "description": "You scan the tactical area..."},
        "map": {"width": width, "height": height, "grid": grid, "biome": "forest"},
        "entities": vtt_entities,
        "log": ["Tactical simulation initiated."]
    }

@app.get("/char/{name}")
def get_character(name: str):
    player = next((e for e in world_ecs.entities.values() if e.name.lower() == name.lower()), None)
    if player: return player.to_dict()
    
    save_path = os.path.join(DATA_DIR, "Saves", f"{name}.json")
    if os.path.exists(save_path):
        with open(save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Character not found.")

@app.get("/tactical/state", response_model=TacticalStateResponse)
def get_tactical_state():
    if not db.active_combat: raise HTTPException(status_code=404, detail="No active tactical session found.")
    
    player_c = next((c for c in db.active_combat.combatants if "player" in c.name), None)
    if not player_c: raise HTTPException(status_code=404, detail="Player not found in active combat.")
    
    player_stats = PlayerTacticalStats(
        name=player_c.name,
        health=TacticalHealth(current=player_c.hp, max=player_c.max_hp),
        stamina=TacticalHealth(current=player_c.sp, max=player_c.max_sp),
        focus=TacticalHealth(current=player_c.fp, max=player_c.max_fp),
        composure=TacticalHealth(current=player_c.cmp, max=player_c.max_cmp),
        coordinates=TacticalCoords(x=player_c.x, y=player_c.y),
        attributes=player_c.get_component(Stats).attrs if player_c.has_component(Stats) else {}
    )
    
    enemy_list = [
        EnemyState(
            id=c.id, name=c.name, type="Enemy",
            health=TacticalHealth(current=c.hp, max=c.max_hp),
            coordinates=TacticalCoords(x=c.x, y=c.y)
        ) for c in db.active_combat.combatants if "enemy" in c.name
    ]
    
    return TacticalStateResponse(
        player_stats=player_stats,
        enemy_list=enemy_list,
        active_effects=[]
    )

class SimulationRequest(BaseModel):
    entities: List[Dict[str, Any]]
    years: int = 100

@app.post("/architect/simulate")
async def run_world_simulation(req: SimulationRequest):
    """
    Invokes the C++ Headless Engine to generate history based on the editor's seed state.
    """
    print(f"[ARCHITECT] Initializing Simulation Bridge for {req.years} years...")
    
    # 1. Save Seed State
    seed_path = os.path.join(DATA_DIR, "seed_state.json")
    with open(seed_path, 'w', encoding='utf-8') as f:
        json.dump({"agents": req.entities}, f, indent=4)
    
    # 2. Invoke C++ Engine
    # Path to the engine relative to the workspace root
    engine_path = os.path.join(TALEWEAVERS_ROOT, "FantasyLloreAndWorldSimulator", "bin", "TALEWEAVERS_Engine.exe")
    
    if not os.path.exists(engine_path):
        # Fallback to local dev bin if exists
        engine_path = os.path.join(TALEWEAVERS_ROOT, "bin", "TALEWEAVERS_Engine.exe")

    if not os.path.exists(engine_path):
        print(f"[ERROR] Simulation Engine not found at {engine_path}")
        raise HTTPException(status_code=500, detail="Simulation Engine executable missing.")

    import subprocess
    try:
        # We pass the number of years as an argument
        print(f"[ARCHITECT] Executing {engine_path}...")
        proc = subprocess.run([engine_path, str(req.years)], capture_output=True, text=True, timeout=300)
        
        if proc.returncode != 0:
            print(f"[ERROR] Engine Failed: {proc.stderr}")
            raise HTTPException(status_code=500, detail=f"Simulation Engine error: {proc.stderr}")
            
        print("[ARCHITECT] Simulation Successful. History generated.")
        
        # 3. Synchronize ECS (ETL Bridge)
        from core.import_world import WorldImporter
        importer = WorldImporter()
        importer.clear_world()
        
        # C++ Engine saves its final state to gamestate.json in the data hub
        # Here we assume the engine uses the standardized export path we discussed
        master_export = os.path.join(DATA_DIR, "master_export.json")
        # For now, let's just trigger the importer on whatever the engine dropped
        importer.import_entities(master_export)
        
        # Reload ECS registry
        world_ecs.load_all()
        
        return {
            "status": "success", 
            "log": proc.stdout.splitlines()[-10:],
            "years_simulated": req.years
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Simulation timed out.")
    except Exception as e:
        print(f"[ERROR] Simulation Bridge Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/architect/history/list")
async def list_world_history():
    """Returns a list of years available in the simulation history."""
    history_dir = os.path.join(DATA_DIR, "history")
    if not os.path.exists(history_dir):
        return {"years": []}
    
    files = os.listdir(history_dir)
    years = []
    for f in files:
        if f.startswith("year_") and f.endswith(".map"):
            try:
                year = int(f.replace("year_", "").replace(".map", ""))
                years.append(year)
            except: continue
            
    return {"years": sorted(years)}

@app.post("/architect/history/load/{year}")
async def load_historical_year(year: int):
    """Loads a specific historical snapshot into the active ECS state."""
    print(f"[ARCHITECT] Scrubbing to Year {year}...")
    
    snapshot_path = os.path.join(DATA_DIR, "history", f"year_{year}.map")
    if not os.path.exists(snapshot_path):
        raise HTTPException(status_code=404, detail=f"History snapshot for year {year} not found.")

    engine_path = os.path.join(TALEWEAVERS_ROOT, "FantasyLloreAndWorldSimulator", "bin", "TALEWEAVERS_Engine.exe")
    if not os.path.exists(engine_path):
        engine_path = os.path.join(TALEWEAVERS_ROOT, "bin", "TALEWEAVERS_Engine.exe")

    import subprocess
    try:
        # Run engine in export mode to generate master_export.json for this year
        print(f"[ARCHITECT] Running engine export for: {snapshot_path}")
        proc = subprocess.run([engine_path, "--export", snapshot_path], capture_output=True, text=True, timeout=30)
        
        if proc.returncode != 0:
            print(f"[ERROR] Engine Export Failed: {proc.stderr}")
            raise HTTPException(status_code=500, detail="Failed to export historical state.")

        # Sync master_export.json back to ECS
        from core.import_world import WorldImporter
        importer = WorldImporter()
        importer.clear_world()
        
        master_export = os.path.join(DATA_DIR, "master_export.json")
        importer.import_entities(master_export)
        
        # Refresh registry
        world_ecs.load_all()
        
        return {"status": "success", "year": year}
        
    except Exception as e:
        print(f"[ERROR] Scrubbing Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PaintRequest(BaseModel):
    x: int
    y: int
    tile_index: int
    radius: int = 2

@app.get("/architect/grid")
def get_architect_grid():
    if not db.world_grid: raise HTTPException(status_code=503, detail="Grid System Offline.")
    return {
        "width": db.world_grid.width,
        "height": db.world_grid.height,
        "grid": db.world_grid.grid
    }

@app.post("/architect/paint")
def paint_architect_grid(req: PaintRequest):
    if not db.world_grid: raise HTTPException(status_code=503, detail="Grid System Offline.")
    db.world_grid.paint(req.x, req.y, req.tile_index, req.radius)
    db.world_grid.save()
    return {"status": "success"}

@app.post("/architect/sync/vault")
async def sync_vault():
    """
    Triggers the Vault Compiler to index Obsidian notes and auto-populate the world.
    """
    from tools.vault_compiler import VaultCompiler, VAULT_PATH, DB_PATH
    try:
        compiler = VaultCompiler(VAULT_PATH, DB_PATH)
        compiler.compile()
        compiler.auto_populate()
        
        # Refresh registry and RAG
        world_ecs.load_all()
        if db.rag:
            db.rag = SimpleRAG(data_path=os.path.join(DATA_DIR, "lore"), async_init=False)
            
        return {"status": "success", "message": "Vault synchronized and world auto-populated."}
    except Exception as e:
        print(f"[ERROR] Vault Sync Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
def refresh_data():
    db.load()
    return {"status": "refreshed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
