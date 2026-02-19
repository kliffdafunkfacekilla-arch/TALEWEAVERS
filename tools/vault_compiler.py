import os
import json
import sqlite3
import frontmatter
import uuid
import random

# Configuration
VAULT_PATH = os.path.join(os.getcwd(), "data", "lore")
DB_PATH = os.path.join(os.getcwd(), "data", "world_state.db")

class VaultCompiler:
    def __init__(self, vault_path, db_path):
        self.vault_path = vault_path
        self.db_path = db_path
        self.registry = {} # type -> list of entries

    def compile(self):
        print(f"[VOULT] Compiling vault from {self.vault_path}...")
        for root, dirs, files in os.walk(self.vault_path):
            category = os.path.basename(root)
            for file in files:
                if file.endswith(".md"):
                    self._process_note(os.path.join(root, file), category)
        
        print(f"[VOULT] Compiled {sum(len(v) for v in self.registry.values())} notes.")
        self._sync_to_db()

    def _process_note(self, filepath, category):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
            entry = {
                "id": post.get("id", os.path.basename(filepath).replace(".md", "")),
                "title": post.get("title", os.path.basename(filepath).replace(".md", "")),
                "type": post.get("type", category),
                "content": post.content,
                "metadata": post.metadata,
                "tags": post.get("tags", []),
                "associated_nodes": post.get("associated_nodes", []),
                "is_procedural": post.get("is_procedural", False)
            }
            
            # Map attributes for seeding
            entry["temp_pref"] = post.get("temp_pref", [0, 100])
            entry["moisture_pref"] = post.get("moisture_pref", [0, 100])
            
            if entry["type"] not in self.registry:
                self.registry[entry["type"]] = []
            self.registry[entry["type"]].append(entry)
            
        except Exception as e:
            print(f"  [!] Error processing {filepath}: {e}")

    def _sync_to_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure lore table has the right schema (similar to sync_db.py but with metadata)
        cursor.execute("DROP TABLE IF EXISTS lore")
        cursor.execute("""
            CREATE TABLE lore (
                id TEXT PRIMARY KEY,
                title TEXT,
                type TEXT,
                narrative TEXT,
                data TEXT
            )
        """)
        
        for cat, entries in self.registry.items():
            for entry in entries:
                cursor.execute("""
                    INSERT INTO lore (id, title, type, narrative, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entry["id"],
                    entry["title"],
                    entry["type"],
                    entry["content"],
                    json.dumps(entry)
                ))
        
        conn.commit()
        conn.close()
        print(f"[VOULT] Synced to {self.db_path}.")

    def auto_populate(self):
        """
        Procedural Seeding Function.
        Matches agents/resources to biomes based on world_grid data.
        """
        print("[VOULT] Running High-Fidelity Biome-Matched Seeding...")
        
        # 1. Load the Grid
        grid_path = os.path.join(os.getcwd(), "data", "world_grid.json")
        if not os.path.exists(grid_path):
            print("[ERROR] world_grid.json not found. Cannot seed without map data.")
            return

        with open(grid_path, 'r') as f:
            grid_data = json.load(f)
            grid = grid_data['grid']
            width = grid_data['width']
            height = grid_data['height']

        # 2. Biome Metric Mapping (Translation Layer)
        # Based on WorldArchitect brushes: 896=Mtn, 194=Water, 130=Forest, 128=Grass
        TILE_METRICS = {
            896: {"temp": 40, "moisture": 10}, # Cold/Dry Mountain
            194: {"temp": 60, "moisture": 100}, # Warm Water
            130: {"temp": 65, "moisture": 70}, # Temperate Forest
            128: {"temp": 70, "moisture": 40}, # Grassland
            # Add implicit 'desert' if we see a specific index later
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        templates = []
        for cat in self.registry:
            templates.extend(self.registry[cat])
            
        placed_count = 0
        for template in templates:
            t_pref = template.get("temp_pref", [0, 100])
            m_pref = template.get("moisture_pref", [0, 100])
            
            # Find matching cells in the grid
            valid_cells = []
            for y in range(height):
                for x in range(width):
                    tile_idx = grid[y][x]
                    metrics = TILE_METRICS.get(tile_idx, {"temp": 50, "moisture": 50}) # Neutral fallback
                    
                    if (t_pref[0] <= metrics["temp"] <= t_pref[1] and 
                        m_pref[0] <= metrics["moisture"] <= m_pref[1]):
                        valid_cells.append((x, y))

            if not valid_cells:
                continue

            # Seed based on density/poisson-ish sampling
            # For each template, try to place a few instances
            num_to_place = min(len(valid_cells), random.randint(3, 8))
            sample_cells = random.sample(valid_cells, num_to_place)

            for x, y in sample_cells:
                entity_id = str(uuid.uuid4())
                entity_data = {
                    "id": entity_id,
                    "name": template["title"],
                    "tags": template["tags"] + ["procedural"],
                    "metadata": {
                        "source_lore": template["id"],
                        "is_procedural": True
                    },
                    "components": {
                        "Position": {"x": x, "y": y, "z": 0},
                        "Renderable": {
                            "icon": template.get("metadata", {}).get("icon", "sheet:5074"),
                            "color": "#ffffff"
                        }
                    }
                }
                
                cursor.execute('INSERT OR REPLACE INTO entities (id, name, data) VALUES (?, ?, ?)',
                              (entity_id, template["title"], json.dumps(entity_data)))
                placed_count += 1
        
        conn.commit()
        conn.close()
        print(f"[VOULT] Procedurally seeded {placed_count} entities using Biome-Matching.")

if __name__ == "__main__":
    compiler = VaultCompiler(VAULT_PATH, DB_PATH)
    compiler.compile()
    compiler.auto_populate()
