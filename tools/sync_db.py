import json
import sqlite3
import os

DATA_HUB = os.path.join(os.getcwd(), "data")
LORE_PATH = os.path.join(DATA_HUB, "lore")
DB_PATH = os.path.join(DATA_HUB, "world_state.db")
JSON_STATE_PATH = os.path.join(DATA_HUB, "compiled_world.json")

def sync():
    if not os.path.exists(LORE_PATH):
        print(f"[ERROR] {LORE_PATH} not found. Run the C++ simulation first.")
        # Ensure directory structure if it doesn't exist
        os.makedirs(os.path.join(LORE_PATH, "history"), exist_ok=True)
        return

    print(f"[SYNC] Connecting to {DB_PATH} and indexing Atomic Lore...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Wipe and Prepare Tables
    cursor.execute("DROP TABLE IF EXISTS entities")
    cursor.execute("DROP TABLE IF EXISTS lore")
    
    cursor.execute("""
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location INTEGER,
            culture_id INTEGER,
            population INTEGER,
            aggression REAL,
            structure_type INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE lore (
            id TEXT PRIMARY KEY,
            title TEXT,
            year INTEGER,
            tags TEXT,
            nodes TEXT,
            content TEXT,
            importance REAL,
            category TEXT
        )
    """)

    # 2. Sync Physical Simulation State (Entities)
    if os.path.exists(JSON_STATE_PATH):
        with open(JSON_STATE_PATH, "r") as f:
            world = json.load(f)
            print(f"[SYNC] Injecting {len(world.get('entities', []))} surviving entities...")
            for ent in world.get("entities", []):
                cursor.execute("""
                    INSERT INTO entities (location, culture_id, population, aggression, structure_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (ent["location"], ent["culture_id"], ent["population"], ent["aggression"], ent.get("structure", 0)))

    # 3. Index Atomic Lore Pieces from Directory
    print("[SYNC] Scanning Lore Knowledge Graph...")
    indexed_count = 0
    for root, dirs, files in os.walk(LORE_PATH):
        category = os.path.basename(root)
        for file in files:
            if file.endswith(".json"):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        entry = json.load(f)
                        cursor.execute("""
                            INSERT INTO lore (id, title, year, tags, nodes, content, importance, category)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry.get("id"),
                            entry.get("title"),
                            entry.get("last_sim_update", 0),
                            ",".join(entry.get("tags", [])),
                            ",".join(entry.get("associated_nodes", [])),
                            entry.get("content"),
                            entry.get("importance", 0.5),
                            category
                        ))
                        indexed_count += 1
                except Exception as e:
                    print(f"  [!] Error indexing {file}: {e}")

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Database sync complete. {indexed_count} atomic lore pieces indexed.")

if __name__ == "__main__":
    sync()
