import os
import sys
import json
from typing import Dict, Any

# --- PATH TUNING ---
BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
TALEWEAVERS_ROOT = os.path.dirname(BRAIN_DIR)
DATA_DIR = os.path.join(TALEWEAVERS_ROOT, "data")
CORE_DIR = os.path.join(TALEWEAVERS_ROOT, "core")

if TALEWEAVERS_ROOT not in sys.path: sys.path.append(TALEWEAVERS_ROOT)
if CORE_DIR not in sys.path: sys.path.append(CORE_DIR)
if BRAIN_DIR not in sys.path: sys.path.append(BRAIN_DIR)

from campaign_system import CampaignGenerator
from core.sensory_layer import SensoryLayer
from core.item_generator import ItemGenerator
from core.quest_manager import QuestManager
from world.sim_manager import SimulationManager
from core.memory import MemoryManager
from world.graph_manager import WorldGraph
from core.database import PersistenceLayer
from core.rag import SimpleRAG
from workflow.gamestate_machine import SagaGameLoop
from core.ecs import world_ecs
from core.world_grid import WorldGrid
from core.definition_registry import DefinitionRegistry

LORE_PATH = os.path.join(DATA_DIR, "lore.json")
GAMESTATE_PATH = os.path.join(DATA_DIR, "gamestate.json")

class WorldDatabase:
    def __init__(self):
        self.lore = []
        self.gamestate = {}
        self.factions = {}
        self.nodes = []
        
        # Core Services
        self.campaign_gen = CampaignGenerator(save_dir=os.path.join(DATA_DIR, "Saves"))
        self.sensory = SensoryLayer(model="qwen2.5:latest")
        self.item_gen = ItemGenerator(os.path.join(DATA_DIR, "Item_Builder.json"))
        self.quests = QuestManager(os.path.join(DATA_DIR, "quests.json"))
        self.db = PersistenceLayer(os.path.join(DATA_DIR, "world_state.db"))
        self.world_grid = WorldGrid(width=100, height=100, save_path=os.path.join(DATA_DIR, "world_grid.json"))
        self.definitions = DefinitionRegistry(DATA_DIR)
        
        # State & Logic
        self.active_combat = None
        self.sim = None
        self.memory = None
        self.graph = None
        self.rag = None
        self.loop = None
    
    def load(self):
        print(f"[BOOT] Initializing World Database Services...")
        
        # 1. Initialize RAG (v2.0 Atomic Folder)
        lore_dir = os.path.join(DATA_DIR, "lore")
        if os.path.exists(lore_dir):
            print(f"[BOOT] RAG: Loading Atomic Knowledge Graph...")
            self.rag = SimpleRAG(data_path=lore_dir, async_init=True)
        elif os.path.exists(LORE_PATH):
            print(f"[BOOT] RAG: Falling back to legacy lore.json")
            with open(LORE_PATH, 'r', encoding='utf-8') as f:
                self.lore = json.load(f)
            self.rag = SimpleRAG(lore_data=self.lore, async_init=True)

        # 2. Load World State
        try:
            if os.path.exists(GAMESTATE_PATH):
                with open(GAMESTATE_PATH, 'r', encoding='utf-8') as f:
                    self.gamestate = json.load(f)
                self.factions = {f['id']: f for f in self.gamestate.get('factions', [])}
                self.nodes = self.gamestate.get('nodes', [])
            
            self.quests.load()
            self.sim = SimulationManager(self.gamestate)
            self.memory = MemoryManager(self.sensory)
            self.graph = WorldGraph(self.nodes)
            self.db.sync_nodes(self.nodes)

            # 3. Initialize Game Loop
            self.loop = SagaGameLoop(
                self.sensory, 
                lambda: self.active_combat,
                self.rag, 
                self.memory,
                self.sim,
                self.quests
            )

            # 4. Restore ECS (SQLite)
            world_ecs.load_all()
            
            # 5. Load Asset Definitions
            self.definitions.load_all()
            
        except Exception as e:
            print(f"[ERROR] Database Hydration Failed: {e}")

# Global Singleton
db = WorldDatabase()

def get_db():
    return db

def get_ecs():
    return world_ecs
