import json
import os
import sys

# Ensure we can find the Global Config
BRAIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BRAIN_ROOT, "data"))
try:
    import SagaConfig
    HUB_ENABLED = True
except ImportError:
    HUB_ENABLED = False

from core.world_math import WorldCoords

class GameState:
    """
    Manages player data and world persistence.
    Synced with the SAGA Global Data Hub.
    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        if HUB_ENABLED:
            self.saves_dir = os.path.join(SagaConfig.DATA_HUB, "Saves")
        else:
            self.saves_dir = os.path.join(base_dir, "Saves")
            
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
            
        self.coords = WorldCoords() # Default at [0, 50, 50, 50, 50]
        
        self.player = {
            "Name": "Hero",
            "Species": "Human",
            "Level": 1,
            "HP": 100,
            "SP": 50,
            "FP": 50,
            "CMP": 0,
            "Coordinates": self.coords.to_dict(),
            "Powers": [],
            "Skills": ["Might", "Reflexes"],
            "Inventory": []
        }

    def get_player(self):
        return self.player

    def update_player(self, data):
        self.player.update(data)
        self.save_character()

    def get_saves_dir(self):
        return self.saves_dir

    def save_character(self):
        name = self.player.get("Name", "Hero")
        path = os.path.join(self.saves_dir, f"{name}.json")
        with open(path, 'w') as f:
            json.dump(self.player, f, indent=4)

    def load_character(self, name):
        path = os.path.join(self.saves_dir, f"{name}.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.player = json.load(f)
            return True
        return False
