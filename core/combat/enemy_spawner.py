import os
import sys
import random
import json

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../Data")
TEMP_DIR = os.path.join(BASE_DIR, "../../Saves/temp")

# Ensure temp dir
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

# --- DATA LOADER (Simplified from charcreate.py) ---
def load_csv(path):
    import csv
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return list(csv.DictReader(f))
    except: return []

class EnemySpawner:
    def __init__(self):
        self.species_stats = {}
        self.evolutions = {}
        self.skills = []
        self.talents = []
        self.tool_types = []
        self.weapon_groups = []
        self.load_data()
        
    def load_data(self):
        # Species Base Stats
        for sp in ["Mammal", "Avian", "Reptile", "Aquatic", "Insect", "Plant"]:
            rows = load_csv(os.path.join(DATA_DIR, f"{sp}.csv"))
            if rows:
                self.species_stats[sp] = rows[0] if rows else {}
                self.evolutions[sp] = rows
                
        # Skills & Talents
        self.skills = load_csv(os.path.join(DATA_DIR, "Skills.csv"))
        self.talents = load_csv(os.path.join(DATA_DIR, "Talents.csv"))
        self.tool_types = load_csv(os.path.join(DATA_DIR, "Tool_types.csv"))
        self.weapon_groups = load_csv(os.path.join(DATA_DIR, "Weapon_Groups.csv"))
        
        # --- NEW: BEAST DATA ---
        beast_path = os.path.join(BASE_DIR, "../../Web_ui/public/data/Beast_Encounter.json")
        try:
            with open(beast_path, 'r') as f:
                self.beast_data = json.load(f)
        except:
            self.beast_data = []

    def spawn_beast(self, beast_id=None, biome="DUNGEON", level=1):
        """
        Spawns a specific or random beast from the JSON encounter table.
        """
        if not self.beast_data: return self.generate() # Fallback
        
        selected = None
        if beast_id:
            for b in self.beast_data:
                if b.get("Entity_ID") == beast_id:
                    selected = b; break
        
        if not selected:
            from world.stubs import EncounterTable
            selected = EncounterTable.get_weighted_beast(self.beast_data, biome, level)
            
        if not selected: return self.generate()

        name = f"{selected.get('Family_Name')} {selected.get('Role')}"
        species = selected.get("Type", "Mammal")
        
        # Hydrate Stats from Beast JSON
        stats = {
            "Might": int(float(selected.get("Might", 10))),
            "Endurance": int(float(selected.get("Endure", 10))),
            "Finesse": int(float(selected.get("Finesse", 10))),
            "Reflexes": int(float(selected.get("Reflex", 10))),
            "Vitality": int(float(selected.get("Vitality", 10))),
            "Fortitude": int(float(selected.get("Fortitude", 10))),
            "Knowledge": int(float(selected.get("Knowledge", 5))),
            "Logic": int(float(selected.get("Logic", 5))),
            "Awareness": int(float(selected.get("Aware", 5))),
            "Intuition": int(float(selected.get("Intuit", 5))),
            "Charm": int(float(selected.get("Charm", 5))),
            "Willpower": int(float(selected.get("Will", 5)))
        }
        
        # Scaling
        if level > 1:
            for k in stats: stats[k] += (level - 1)

        # Derive
        hp = 20 + stats["Vitality"] * 3
        speed = int(float(selected.get("Move_Speed", "30").split()[0]))
        
        data = {
            "Name": name,
            "Species": species,
            "Stats": stats,
            "Derived": {"HP": hp, "Speed": speed, "SP": 20, "FP": 20, "CMP": 20},
            "Traits": [name, species],
            "Powers": [],
            "Skills": ["Natural Weapons"],
            "Inventory": [],
            "AI": "Aggressive"
        }
        
        # Return data directly
        return data

    def generate(self, ai_template="Aggressive"):
        """
        Generate a random enemy combatant and save to temp JSON.
        Returns the path to the generated file.
        """
        name = f"Enemy_{random.randint(100, 999)}"
        
        # 1. Species
        species_list = list(self.species_stats.keys())
        if not species_list: species_list = ["Mammal"]
        species = random.choice(species_list)
        
        # Base Stats (from evolution rows)
        stats = {"Might": 10, "Reflexes": 10, "Vitality": 10, "Knowledge": 5, "Willpower": 5}
        base_row = self.species_stats.get(species, {})
        for k in stats:
            if k in base_row:
                try: stats[k] = int(base_row[k])
                except: pass
        
        # 2. Derive
        hp = 10 + stats.get("Vitality", 0) * 2
        speed = 20 + stats.get("Reflexes", 0)
        sp = 10
        fp = 10
        cmp = 10
        
        # 3. Traits (pick 1-2 from Talents)
        traits = []
        if self.talents:
            picks = random.sample(self.talents, min(2, len(self.talents)))
            traits = [p.get("Talent_Name") for p in picks if p.get("Talent_Name")]
        
        # 4. Inventory (random weapon)
        inventory = []
        if self.weapon_groups:
            group = random.choice(self.weapon_groups)
            # Parse 'Examples' column for valid item names
            examples_raw = group.get("Examples", "Sword")
            candidates = [x.strip() for x in examples_raw.split(',') if x.strip()]
            
            wpn = random.choice(candidates) if candidates else "Sword"
            inventory.append(wpn)
        
        # 5. AI Template
        # This is a simple string stored in the data; the Engine will interpret it.
        ai = ai_template
        
        # Build Data
        data = {
            "Name": name,
            "Species": species,
            "Stats": stats,
            "Derived": {"HP": hp, "Speed": speed, "SP": sp, "FP": fp, "CMP": cmp},
            "Traits": traits,
            "Powers": [],
            "Skills": ["Guard"],
            "Inventory": inventory,
            "AI": ai
        }
        
        # Return data directly
        return data

# Singleton
spawner = EnemySpawner()

# --- AI TEMPLATES DEFINITIONS ---
AI_TEMPLATES = {
    "Aggressive": "Charge and attack every turn.",
    "Defensive": "Defend until attacked, then retaliate.",
    "Ranged": "Stay at max distance and use ranged attacks.",
    "Support": "Buff allies, avoid direct combat.",
    "Berserker": "Attack randomly, ignoring tactics.",
}

def get_ai_templates():
    return list(AI_TEMPLATES.keys())

if __name__ == "__main__":
    print("Generating test enemy...")
    data = spawner.generate("Aggressive")
    print(f"Generated: {data.get('Name')}")
