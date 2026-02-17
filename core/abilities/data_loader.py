import sys
import os
import json

# Ensure we can find the Global Config
BRAIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BRAIN_ROOT, "data"))
try:
    import SagaConfig
except ImportError:
    SagaConfig = None

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = data_dir
        elif SagaConfig:
            self.data_dir = SagaConfig.TACTICAL_DATA
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "../../Data")
        
        self.ttis_data = {}
        
        # Data Containers
        self.skills = []
        self.talents = []
        self.schools = []
        self.species_skills = {}
        self.power_tiers = {} 
        self.power_shapes = {}
        self.weapon_mastery = {}
        self.armor_mastery = {}
        self.tool_mastery = {}

        self.reload_all()

    def reload_all(self):
        # Load Primary Rules JSON
        path = os.path.join(self.data_dir, "ttis.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.ttis_data = json.load(f)
        
        # Extract Skills from Command Grid (The new Source of Truth)
        if "command_grid" in self.ttis_data:
            self._extract_skills_from_grid(self.ttis_data["command_grid"])

        # Load Logic-Based JSONs (if exist)
        self._load_json_list("Schools_of_Power.json", self.schools)
        # self._load_json_list("Talents.json", self.talents) # Only if migrated
        
        # Setup Defaults for Power Scaling (Hardcoded for logic integrity if files missing)
        self._init_power_defaults()

    def _extract_skills_from_grid(self, grid):
        """Recursively find skills in the decision tree."""
        for category in grid.values():
            for subcat in category.values():
                if "skills" in subcat:
                    for s in subcat["skills"]:
                        # Convert to flat dict for lookups
                        self.skills.append({
                            "Skill_Name": s["name"],
                            "Attribute": s["pair"][0].upper(), # Use lead stat
                            "Description": s["effect"]
                        })

    def _load_json_list(self, filename, target_list):
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        target_list.extend(data)
            except:
                pass

    def _init_power_defaults(self):
        # Minimal scaling logic for engine stability
        for tier in range(1, 6):
            self.power_tiers[tier] = {
                "damage_dice": f"{tier}d6",
                "resource_cost": tier,
                "force": "5 ft" 
            }
        self.power_shapes = {
            1: {"range": "Melee"},
            2: {"range": "15 ft"},
            3: {"range": "30 ft"}
        }

    # ==================== ACCESSORS ====================
    
    def get_tier_damage(self, tier):
        return self.power_tiers.get(tier, {}).get("damage_dice", f"{tier}d6")
    
    def get_tier_cost(self, tier):
        return self.power_tiers.get(tier, {}).get("resource_cost", tier)

if __name__ == "__main__":
    dl = DataLoader()
    print(f"Loaded {len(dl.skills)} Skills from TTIS.json")

