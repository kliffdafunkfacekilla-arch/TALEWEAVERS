import sqlite3
import json
import os

class PersistenceLayer:
    """
    Handles SQLite persistence for the active game world.
    Prevents JSON bottlenecks and corruption.
    """
    def __init__(self, db_path="data/world_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        directory = os.path.dirname(self.db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Entities Table (ECS Pattern) - Updated for 4-Layer Hierarchy
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                layer_id INTEGER DEFAULT 0, -- 0: Global, 1: Regional, 2: Local, 3: Player
                location_id TEXT, -- UUID of the zone/region this entity is in
                data TEXT -- Serialized components
            )
        ''')
        
        self._ensure_columns(cursor)
        
        # 1. Global Layer (30 Regions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_regions (
                id INTEGER PRIMARY KEY,
                name TEXT,
                grid_x INTEGER,
                grid_y INTEGER,
                biome_data TEXT,
                political_data TEXT
            )
        ''')

        # 2. Regional/Local Layer (100x100 Zones per Global Region)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS local_zones (
                id TEXT PRIMARY KEY,
                global_region_id INTEGER,
                region_x INTEGER,
                region_y INTEGER,
                terrain_data TEXT,
                FOREIGN KEY(global_region_id) REFERENCES global_regions(id)
            )
        ''')

        # 3. Player Layer (Battle Maps)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_maps (
                id TEXT PRIMARY KEY,
                local_zone_id TEXT,
                local_x INTEGER,
                local_y INTEGER,
                map_data TEXT, -- Walls, lighting, specific objects
                FOREIGN KEY(local_zone_id) REFERENCES local_zones(id)
            )
        ''')
        
        # Nodes Table (Legacy Graph - Keeping for compatibility during migration)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT,
                x INTEGER,
                y INTEGER,
                faction_id TEXT,
                state TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def _ensure_columns(self, cursor):
        """Migration helper to ensure columns exist in existing tables."""
        try:
            cursor.execute('ALTER TABLE entities ADD COLUMN layer_id INTEGER DEFAULT 0')
        except sqlite3.OperationalError: pass
        try:
            cursor.execute('ALTER TABLE entities ADD COLUMN location_id TEXT')
        except sqlite3.OperationalError: pass

    def save_entity(self, entity_id, name, data_dict, layer_id=0, location_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        self._ensure_columns(cursor)

        cursor.execute('''
            INSERT OR REPLACE INTO entities (id, name, data, layer_id, location_id) 
            VALUES (?, ?, ?, ?, ?)
        ''', (entity_id, name, json.dumps(data_dict), layer_id, location_id))
        conn.commit()
        conn.close()

    def load_entity(self, entity_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        self._ensure_columns(cursor)
        cursor.execute('SELECT name, data FROM entities WHERE id = ?', (entity_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"name": row[0], "data": json.loads(row[1])}
        return None

    def load_all_entities(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        self._ensure_columns(cursor)
        cursor.execute('SELECT id, name, data, layer_id, location_id FROM entities')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def sync_nodes(self, nodes_list):
        """Batch update world nodes from JSON to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for node in nodes_list:
            cursor.execute('''
                INSERT OR REPLACE INTO nodes (id, name, x, y, faction_id, state)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (node.get('id'), node.get('name'), node.get('x'), node.get('y'), 
                  node.get('faction_id'), json.dumps(node.get('stats', {}))))
        conn.commit()
        conn.close()
        print(f"[DB] Synced {len(nodes_list)} nodes to SQLite.")

    def create_global_region(self, region_id, name, grid_x, grid_y, biome_data, political_data=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO global_regions (id, name, grid_x, grid_y, biome_data, political_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (region_id, name, grid_x, grid_y, json.dumps(biome_data), json.dumps(political_data or {})))
        conn.commit()
        conn.close()

    def get_global_regions(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, grid_x, grid_y, biome_data FROM global_regions')
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "grid_x": r[2], "grid_y": r[3], "biome_data": json.loads(r[4])} for r in rows]

    def create_local_zone(self, zone_id, global_region_id, region_x, region_y, terrain_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO local_zones (id, global_region_id, region_x, region_y, terrain_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (zone_id, global_region_id, region_x, region_y, json.dumps(terrain_data)))
        conn.commit()
        conn.close()

    def get_local_zones(self, global_region_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, region_x, region_y, terrain_data FROM local_zones WHERE global_region_id = ?', (global_region_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "region_x": r[1], "region_y": r[2], "terrain_data": json.loads(r[3])} for r in rows]

    def create_player_map(self, map_id, local_zone_id, local_x, local_y, map_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO player_maps (id, local_zone_id, local_x, local_y, map_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (map_id, local_zone_id, local_x, local_y, json.dumps(map_data)))
        conn.commit()
        conn.close()

    def get_player_map(self, map_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, local_zone_id, local_x, local_y, map_data FROM player_maps WHERE id = ?', (map_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "local_zone_id": row[1], "local_x": row[2], "local_y": row[3], "map_data": json.loads(row[4])}
        return None
