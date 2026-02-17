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
    
    def load(self):
        # Load Lore (Static)
        try:
            if os.path.exists(LORE_PATH):
                with open(LORE_PATH, 'r', encoding='utf-8') as f:
                    self.lore = json.load(f)
                print(f"[DATA] Loaded {len(self.lore)} lore entries.")
        except Exception as e:
            print(f"[ERROR] Failed to load lore.json: {e}")

        # Load Gamestate (Dynamic)
        try:
            if os.path.exists(GAMESTATE_PATH):
                with open(GAMESTATE_PATH, 'r', encoding='utf-8') as f:
                    self.gamestate = json.load(f)
                
                self.factions = {f['id']: f for f in self.gamestate.get('factions', [])}
                self.nodes = self.gamestate.get('nodes', [])
                
                meta = self.gamestate.get('meta', {})
                print(f"[DATA] Loaded Gamestate (Epoch: {meta.get('epoch', 0)})")
                
                if self.quests:
                    self.quests.load()
                    print(f"[DATA] Loaded {len(self.quests.quests)} quests.")
            
        except Exception as e:
            print(f"[ERROR] Failed to load gamestate.json: {e}")

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
                        db.quests.update_objective("locate_chest", 1)
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
    try:
        if not db.sensory:
            raise HTTPException(status_code=503, detail="AI Sensory Layer (Ollama) is offline.")
        
        # 1. Resolve Intent
        player_vtt = req.context.get('player', {})
        print(f"[DEBUG] Resolving intent...")
        intent = db.sensory.resolve_intent(req.message, player_vtt)
        action = intent.get("action", "TALK")
        print(f"[DEBUG] Action: {action} | Intent: {intent}")
        
        # 2. Rules Engine Resolution
        visual_updates = []
        mechanical_result = "The world remains still."
        
        if action == "SEARCH":
            print(f"[DEBUG] Executing SEARCH interaction...")
            mechanical_result, v_updates = resolve_mechanical_interaction(action, intent)
            visual_updates.extend(v_updates)
        
        elif db.active_combat:
            player_c = next((c for c in db.active_combat.combatants if c.name == "player_burt"), None)
            
            if action == "MOVE" and player_c:
                params = intent.get("parameters", {})
                dx, dy = params.get("dx", 0), params.get("dy", 0)
                target_x, target_y = player_c.x + dx, player_c.y + dy
                ok, msg = db.active_combat.move_char(player_c, target_x, target_y)
                mechanical_result = msg if isinstance(msg, str) else " ".join(msg)
                if ok:
                    visual_updates.append({"type": "MOVE_TOKEN", "id": "player_burt", "pos": [player_c.x, player_c.y]})
            
            elif action == "ATTACK" and player_c:
                target_id = intent.get("target", "Enemy")
                target_c = next((c for c in db.active_combat.combatants if target_id.lower() in c.name.lower() or target_id.lower() in str(c.data.get("Name","")).lower()), None)
                
                if target_c:
                    res_log = db.active_combat.attack_target(player_c, target_c)
                    mechanical_result = " ".join(res_log)
                    visual_updates.append({"type": "PLAY_ANIMATION", "name": "MELEE_SLASH", "target": target_c.name})
                    visual_updates.append({"type": "UPDATE_HP", "id": target_c.name, "hp": target_c.hp})
                else:
                    mechanical_result = f"You swing at shadows; {target_id} is nowhere to be found."

        # 3. Generate Narrative Response
        print(f"[DEBUG] Generating narrative with result: {mechanical_result}")
        try:
            response = db.sensory.generate_narrative(
                action_result=mechanical_result,
                world_context={
                    "chaos": db.gamestate.get('meta', {}).get('chaos_level', 0.5),
                    "position": req.context.get('world_pos', [500, 500]),
                    "intent": intent,
                    "visible_objects": getattr(db.active_combat, 'world_objects', []) if db.active_combat else [],
                    "active_quests": db.quests.get_active_quests() if db.quests else []
                },
                persona="The Oracle: Visceral and Direct"
            )
        except Exception as e:
            print(f"[ERROR] Narrative generation failed: {e}")
            response = f"The World Oracle remains silent, but the resonance of your action lingers: {mechanical_result}"
        
        print(f"[DEBUG] dm_action success")
        return {
            "intent": intent,
            "narrative": response,
            "visual_updates": visual_updates,
            "mechanical_log": mechanical_result
        }
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

@app.post("/refresh")
def refresh_data():
    db.load()
    return {"status": "refreshed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
