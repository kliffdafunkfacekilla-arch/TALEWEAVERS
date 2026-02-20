import sys
import os
import json
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import PersistenceLayer

def test_hierarchy():
    print("Initializing Test Database...")
    db_path = "test_hierarchy.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = PersistenceLayer(db_path)
    
    # 1. Test Global Region
    print("Testing Global Region...")
    db.create_global_region(1, "Test Region", 5, 5, {"biome": "Forest"}, {"owner": "Elves"})
    regions = db.get_global_regions()
    assert len(regions) == 1
    assert regions[0]["name"] == "Test Region"
    assert regions[0]["biome_data"]["biome"] == "Forest"
    print("PASS: Global Region Created & Retrieved")
    
    # 2. Test Local Zone
    print("Testing Local Zone...")
    db.create_local_zone("zone_01", 1, 10, 10, {"terrain": "Hills"})
    zones = db.get_local_zones(1)
    assert len(zones) == 1
    assert zones[0]["id"] == "zone_01"
    assert zones[0]["terrain_data"]["terrain"] == "Hills"
    print("PASS: Local Zone Created & Retrieved")
    
    # 3. Test Player Map
    print("Testing Player Map...")
    db.create_player_map("map_01", "zone_01", 50, 50, {"walls": []})
    player_map = db.get_player_map("map_01")
    assert player_map is not None
    assert player_map["local_zone_id"] == "zone_01"
    print("PASS: Player Map Created & Retrieved")
    
    # 4. Test Entity with Layer Info
    print("Testing Entity with Layer Info...")
    db.save_entity("ent_01", "Hero", {"hp": 10}, layer_id=3, location_id="map_01")
    entities = db.load_all_entities()
    # id, name, data, layer_id, location_id
    assert len(entities) == 1
    assert entities[0][3] == 3
    assert entities[0][4] == "map_01"
    print("PASS: Entity Saved with Layer Info")
    
    # Cleanup
    print("Cleaning up...")
    os.remove(db_path)
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_hierarchy()
