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
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Entities Table (ECS Pattern)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                data TEXT -- Serialized components
            )
        ''')
        
        # Nodes Table (World Graph)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT,
                x INTEGER,
                y INTEGER,
                faction_id TEXT,
                state TEXT -- JSON blob for dynamic metrics
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_entity(self, entity_id, name, data_dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO entities (id, name, data) VALUES (?, ?, ?)',
                      (entity_id, name, json.dumps(data_dict)))
        conn.commit()
        conn.close()

    def load_entity(self, entity_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, data FROM entities WHERE id = ?', (entity_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"name": row[0], "data": json.loads(row[1])}
        return None

    def load_all_entities(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, data FROM entities')
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
