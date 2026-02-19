import json
import os
import sys
from typing import Dict, List, Any

# Ensure we can import from the core
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from core.ecs import world_ecs, Entity, Position, Renderable, FactionMember, Logistics, Stats, Vitals

class WorldImporter:
    """
    The 'ETL Bridge' between the C++ Architect/Simulator and the Python ECS Runtime.
    Translates 'Master Export' JSON files into persistent SQLite ECS entities.
    """
    def __init__(self, db_path: str = "data/world_state.db"):
        self.registry = world_ecs
        # Ensure we are using the correct DB
        self.registry.db.db_path = db_path

    def clear_world(self):
        """Wipes the existing world state to prepare for a fresh import."""
        print("[IMPORTER] Wiping existing world_state.db...")
        # Simple way to clear: delete the records (handled by PersistenceLayer if we add a clear method)
        # For now, let's just let the persistence layer handle overwrites by ID, 
        # but a hard wipe is cleaner for a 'Master Export' workflow.
        import sqlite3
        conn = sqlite3.connect(self.registry.db.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities")
        conn.commit()
        conn.close()
        self.registry.entities = {}

    def import_entities(self, master_export_path: str):
        """
        Parses the Master Export JSON and seeds the ECS.
        Expects a format like:
        {
            "agents": [{"id": 0, "name": "Orcs", "type": "Civilized", "pos": [100, 150], "pop": 500, ...}],
            "locations": [{"name": "Oakhaven", "pos": [45, 80], "type": "Town", ...}]
        }
        """
        if not os.path.exists(master_export_path):
            print(f"[ERROR] Export file not found: {master_export_path}")
            return

        with open(master_export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"[IMPORTER] Importing world data from {master_export_path}...")

        # 1. Import Factions/Agents (The 'Life' from C++)
        for agent in data.get("agents", []):
            self.create_faction_entity(agent)

        # 2. Import Locations (Towns/Dungeons)
        for loc in data.get("locations", []):
            self.create_location_entity(loc)

        print("[IMPORTER] Import complete.")

    def create_faction_entity(self, data: Dict):
        """Converts a C++ Agent/Culture into a high-level ECS Entity."""
        name = data.get("name", "Unknown Tribe")
        e = Entity(name)
        
        # Position (Map coordinates)
        pos = data.get("pos", [0, 0])
        e.add_component(Position(x=pos[0], y=pos[1]))
        
        # Rendering (Icon from spritesheet)
        icon = "sheet:5076" # Default hostile/agent icon
        if data.get("type") == "Flora": icon = "sheet:896"
        e.add_component(Renderable(icon=icon, scale=1.2))
        
        # Mechanics
        e.add_component(FactionMember(faction=name))
        
        # Simulation Logic (Logistics/Population)
        e.add_component(Logistics(
            resources={"Food": 500, "Gold": 100},
            population=data.get("pop", 100)
        ))
        
        # Tags for indexing
        e.add_tag("faction")
        e.add_tag("simulation_active")
        
        self.registry.add_entity(e)
        print(f"  [+] Seeded Faction: {name}")

    def create_location_entity(self, data: Dict):
        """Converts a POI into a tactical Location entity."""
        name = data.get("name", "Uncharted Site")
        e = Entity(name)
        
        pos = data.get("pos", [0, 0])
        e.add_component(Position(x=pos[0], y=pos[1]))
        
        # Dynamic Icons
        loc_type = data.get("type", "Point of Interest").lower()
        icon = "sheet:2" # Default dungeon
        if "town" in loc_type or "village" in loc_type: icon = "sheet:3"
        elif "tower" in loc_type: icon = "sheet:4"
        
        e.add_component(Renderable(icon=icon, scale=1.5))
        
        # Interactions
        e.add_tag("location")
        e.add_tag("interactive")
        e.metadata["description"] = data.get("description", "A local point of interest.")
        
        self.registry.add_entity(e)
        print(f"  [+] Seeded Location: {name} ({loc_type})")

if __name__ == "__main__":
    importer = WorldImporter()
    # If a seed file exists, auto-import it
    seed_file = "data/master_export.json"
    if os.path.exists(seed_file):
        importer.clear_world()
        importer.import_entities(seed_file)
    else:
        print("[IMPORTER] No master_export.json found in data/. Waiting for C++ Architect export.")
