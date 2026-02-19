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

    def auto_populate(self, map_size=1000):
        """
        Procedural Seeding Function.
        Matches agents/resources to biomes based on preferences.
        """
        print("[VOULT] Running Auto-Populate Seeding...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Register templates from vault
        templates = []
        for cat in self.registry:
            templates.extend(self.registry[cat])
            
        # 2. Procedural Placement
        # In a real scenario, we'd read the Perlin Noise/Heightmap from world_state or similar.
        # For now, we simulate a few placements based on "mock" biome data.
        
        placed_count = 0
        for template in templates:
            # Only seed things with specific prefs
            if "temp_pref" in template or "moisture_pref" in template:
                # Spawn density logic
                for _ in range(5): # Spawn 5 of each matching thing
                    # Mock finding a valid x,y
                    x = random.randint(0, 100)
                    y = random.randint(0, 100)
                    
                    # Flag as procedural
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
                            "Renderable": {"icon": "sheet:5074", "color": "#ffaa00"}
                        }
                    }
                    
                    cursor.execute('INSERT INTO entities (id, name, data) VALUES (?, ?, ?)',
                                  (entity_id, template["title"], json.dumps(entity_data)))
                    placed_count += 1
        
        conn.commit()
        conn.close()
        print(f"[VOULT] Procedurally seeded {placed_count} entities into the world.")

if __name__ == "__main__":
    compiler = VaultCompiler(VAULT_PATH, DB_PATH)
    compiler.compile()
    compiler.auto_populate()
