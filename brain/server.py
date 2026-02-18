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
if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)
if BRAIN_DIR not in sys.path:
    sys.path.append(BRAIN_DIR)

try:
    from campaign_system import CampaignGenerator, POIType, QuestType, CampaignState
    from combat.mechanics import CombatEngine, LegacyCombatant
    from core.sensory_layer import SensoryLayer
    from core.char_creator import CharacterBuilder
    from core.item_generator import ItemGenerator
    from core.quest_manager import QuestManager
    from world.sim_manager import SimulationManager
    from core.memory import MemoryManager
    from world.graph_manager import WorldGraph
    from core.database import PersistenceLayer
    from core.rag import SimpleRAG
    from workflow.gamestate_machine import SagaGameLoop
except ImportError as e:
    print(f"[ERROR] Failed to import internal Core components: {e}")
    CampaignGenerator = None
    CombatEngine = None
    LegacyCombatant = None
    SensoryLayer = None
    CharacterBuilder = None
    ItemGenerator = None
    QuestManager = None

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
        self.db = PersistenceLayer(os.path.join(DATA_DIR, "world_state.db"))
        self.rag = None
        self.loop = None
    
    def load(self):
        # Load Lore (Static)
        try:
            if os.path.exists(LORE_PATH):
                with open(LORE_PATH, 'r', encoding='utf-8') as f:
                    self.lore = json.load(f)
                print(f"[DATA] Loaded {len(self.lore)} lore entries.")
                if SimpleRAG:
                    self.rag = SimpleRAG(self.lore)
                    print("[DATA] RAG Engine Initialized (TF-IDF Index Built).")
        except Exception as e:
            print(f"[ERROR] Failed to load lore.json: {e}")
            import traceback
            traceback.print_exc()

        # Load Gamestate (Dynamic)
        try:
            if os.path.exists(GAMESTATE_PATH):
                with open(GAMESTATE_PATH, 'r', encoding='utf-8') as f:
                    self.gamestate = json.load(f)
                
                self.factions = {f['id']: f for f in self.gamestate.get('factions', [])}
                self.nodes = self.gamestate.get('nodes', [])
                
                meta = self.gamestate.get('meta', {})
                print(f"[DATA] Loaded Gamestate (Epoch: {meta.get('epoch', 0)})")
                print(f"[DATA] Factions: {len(self.factions)} | Nodes: {len(self.nodes)}")
                
                if self.quests:
                    self.quests.load()
                    print(f"[DATA] Loaded {len(self.quests.quests)} quests.")
                
                # Initialize Simulation Manager with loaded state
                if SimulationManager:
                    self.sim = SimulationManager(self.gamestate)
                    print("[DATA] Simulation Manager Initialized (LOD Ready).")
                
                # Initialize Memory Manager
                if MemoryManager and self.sensory:
                    self.memory = MemoryManager(self.sensory)
                    print("[DATA] Memory Manager Initialized.")
                
                # Initialize World Graph
                if WorldGraph:
                    self.graph = WorldGraph(self.nodes)
                    print(f"[DATA] World Graph built with {len(self.nodes)} nodes.")
                
                # Setup SQLite Persistence
                self.db.sync_nodes(self.nodes)

                # Initialize Game Loop (LangGraph Logic)
                if SagaGameLoop and self.sensory:
                    self.loop = SagaGameLoop(
                        self.sensory, 
                        lambda: self.active_combat, # Dynamic Combat Provider 
                        self.rag, 
                        self.memory
                    )
                    print("[DATA] SAGA Game Loop Initialized (LangGraph Pattern).")
            
        except Exception as e:
            print(f"[ERROR] Failed to load gamestate.json: {e}")
            import traceback
            traceback.print_exc()

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
class NewCampaignRequest(BaseModel):
    hero_name: str
    theme: str = "Classic High Fantasy"

class CharCreateRequest(BaseModel):
    name: str
    species: str
    stats: Dict[str, int]

class DMActionRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

# --- TACTICAL STATE MODELS ---
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
    coordinates: TacticalCoords
    attributes: Dict[str, int]

class TacticalStateResponse(BaseModel):
    round: int = 1
    turn_order: List[str] = []
    active_combatant: Optional[str] = None
    player_stats: PlayerTacticalStats
    enemy_list: List[EnemyState]
    active_effects: List[Dict[str, Any]]

# --- HELPER FUNCTIONS ---
def get_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def resolve_mechanical_interaction(action: str, intent: Dict, player_name: str = "Burt"):
    """
    Handles mechanical results for SEARCH/INTERACT intents.
    Returns (mechanical_result_string, visual_updates_list)
    """
    visual_updates = []
    res = "The world remains still."
    
    target_name = intent.get("target", "").lower() if intent else ""
    
    # Check for search/loot interaction
    is_search = action == "SEARCH" or "chest" in target_name or "inspect" in str(intent.get("text", "")).lower()
    
    if is_search:
        if db.item_gen:
            loot = db.item_gen.generate_loot(max_tier=2)
            item_name = loot.get("name", "Glinting Trinket")
            
            # Update Character Save
            save_path = os.path.join(DATA_DIR, "Saves", f"{player_name}.json")
            if os.path.exists(save_path):
                try:
                    with open(save_path, 'r') as f:
                        char_data = json.load(f)
                    
                    if "Inventory" not in char_data:
                        char_data["Inventory"] = []
                    
                    char_data["Inventory"].append(loot)
                    
                    with open(save_path, 'w') as f:
                        json.dump(char_data, f, indent=4)
                    
                    res = f"You searched the area and found: {item_name}!"
                    visual_updates.append({"type": "ADD_ITEM", "item": loot})
                    visual_updates.append({"type": "OPEN_INVENTORY"})
                    
                    # Update Quest Objectives if relevant
                    if db.quests:
                        db.quests.update_objective("open_chest", 1)
                except Exception as e:
                    print(f"[ERROR] Interaction save failed: {e}")
                    res = "You find something, but can't seem to carry it."

    return res, visual_updates

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "SAGA Brain",
        "data": {
            "lore_count": len(db.lore),
            "campaign_active": db.campaign_gen.current_campaign is not None if db.campaign_gen else False,
            "epoch": db.gamestate.get('meta', {}).get('epoch', 0)
        }
    }

@app.post("/dm/action")
async def dm_action(req: DMActionRequest):
    print(f"[DEBUG] dm_action start: {req.message}")
    if not db.loop:
        raise HTTPException(status_code=503, detail="Game Loop Offline.")
    
    try:
        # Execute the Graph Workflow
        result = db.loop.process_turn(req.message, req.context)
        
        print(f"[DEBUG] Workflow Complete. Intent: {result['intent']}")
        return result
    except Exception as e:
        import traceback
        error_msg = f"[CRITICAL ERROR] dm_action failed: {e}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tactical/generate")
def generate_tactical_map(x: int, y: int, poi_id: Optional[str] = None):
    # Simple procedural grid (20x20)
    width, height = 20, 20
    grid = [[1 if (gx == 0 or gx == width-1 or gy == 0 or gy == height-1 or random.random() < 0.1) else 0 for gx in range(width)] for gy in range(height)]
    
    vtt_entities = []
    
    # Initialize Mechanical Rules Engine
    if CombatEngine:
        db.active_combat = CombatEngine(cols=width, rows=height)
        db.active_combat.walls = {(gx, gy) for gy in range(height) for gx in range(width) if grid[gy][gx] == 1}
        
        # Load Player
        burt_path = os.path.join(DATA_DIR, "Saves", "Burt.json")
        if os.path.exists(burt_path):
            with open(burt_path, 'r') as f:
                char_data = json.load(f)
                player_c = LegacyCombatant(data=char_data)
                player_c.name = "player_burt"
                player_c.x, player_c.y = 2, 2
                player_c.team = "Neutral"
                db.active_combat.combatants.append(player_c)
        
        # Add a test enemy
        enemy_c = LegacyCombatant(data={"Name": "Bandit", "Stats": {"Reflexes": 10, "Might": 10, "Vitality": 10}})
        enemy_c.name = "enemy_0"
        enemy_c.x, enemy_c.y = 10, 10
        enemy_c.team = "Enemy"
        db.active_combat.combatants.append(enemy_c)

        vtt_entities = [
            {
                "id": c.name,
                "name": c.data.get("Name", c.name).title(),
                "type": 'player' if c.team == 'Neutral' else 'enemy',
                "pos": [c.x, c.y],
                "hp": getattr(c, 'hp', 20),
                "maxHp": getattr(c, 'max_hp', 20),
                "icon": "icons/race/aquatic_male.png" if c.team == 'Neutral' else "icons/race/human_male.png",
                "tags": ["hero"] if c.team == 'Neutral' else ["hostile"]
            }
            for c in db.active_combat.combatants
        ]

    # Add Objects
    world_objects = [
        {"id": "chest_01", "name": "Ancient Chest", "type": "object", "pos": [width-3, 3], "icon": "icons/object/chest_closed.png", "tags": ["lootable"]},
    ]
    if db.active_combat:
        db.active_combat.world_objects = world_objects
    vtt_entities.extend(world_objects)

    return {
        "meta": {"title": "Wilderness Encounter", "description": "A tactical skirmish.", "world_pos": [x, y]},
        "map": {"width": width, "height": height, "grid": grid, "biome": "forest"},
        "entities": vtt_entities,
        "log": ["Tactical simulation initiated."]
    }

@app.get("/campaign/quests")
async def get_quests():
    return db.quests.get_active_quests() if db.quests else []

@app.post("/world/advance_time")
def advance_world_time(hours: int = Query(1), x: int = Query(500), y: int = Query(500)):
    """
    Advances world time and triggers hierarchical simulation ticks (LOD-aware).
    """
    if not db.sim:
        raise HTTPException(status_code=503, detail="Simulation Engine Offline.")
    
    db.sim.advance_time(hours, player_pos=(x, y))
    
    # Save updated gamestate
    try:
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

@app.get("/tactical/state", response_model=TacticalStateResponse)
def get_tactical_state():
    """
    Returns the current tactical state in the standardized JSON format.
    """
    if not db.active_combat:
        raise HTTPException(status_code=404, detail="No active tactical session found.")
    
    # 1. Map Player
    player_c = next((c for c in db.active_combat.combatants if c.name == "player_burt"), None)
    if not player_c:
        raise HTTPException(status_code=404, detail="Player not found in active combat.")
    
    player_stats = PlayerTacticalStats(
        name=player_c.data.get("Name", "Burt"),
        health=TacticalHealth(current=getattr(player_c, 'hp', 10), max=getattr(player_c, 'max_hp', 10)),
        stamina=TacticalHealth(current=getattr(player_c, 'sp', 10), max=getattr(player_c, 'max_sp', 10)),
        focus=TacticalHealth(current=getattr(player_c, 'fp', 10), max=getattr(player_c, 'max_fp', 10)),
        coordinates=TacticalCoords(x=player_c.x, y=player_c.y),
        attributes=player_c.stats
    )
    
    # 2. Map Enemies
    enemy_list = []
    for c in db.active_combat.combatants:
        if c.team == "Enemy":
            # Extract active effects for this enemy
            effects = []
            status_flags = ["is_staggered", "is_shaken", "is_blinded", "is_stunned", "is_burning", "is_bleeding"]
            for flag in status_flags:
                if getattr(c, flag, False):
                    effects.append({"name": flag.replace("is_", "").title(), "type": "Condition"})
            
            enemy_list.append(EnemyState(
                id=c.name,
                name=c.data.get("Name", "Enemy"),
                type=c.data.get("Type", "Unknown"),
                health=TacticalHealth(current=getattr(c, 'hp', 10), max=getattr(c, 'max_hp', 10)),
                coordinates=TacticalCoords(x=c.x, y=c.y),
                active_effects=effects
            ))
            
    # 3. Global Effects
    active_effects = [] # Placeholder for global environmental effects
    
    # 4. Turn Order
    turn_order = [c.name for c in db.active_combat.turn_order] if hasattr(db.active_combat, 'turn_order') and db.active_combat.turn_order else []
    active_char = db.active_combat.get_active_char()
    active_name = active_char.name if active_char else None

    return TacticalStateResponse(
        round=getattr(db.active_combat, 'round_count', 1),
        turn_order=turn_order,
        active_combatant=active_name,
        player_stats=player_stats,
        enemy_list=enemy_list,
        active_effects=active_effects
    )

@app.post("/refresh")
def refresh_data():
    db.load()
    return {"status": "refreshed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
