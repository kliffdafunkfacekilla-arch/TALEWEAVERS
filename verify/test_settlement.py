import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.ecs import ECSRegistry, Demographics, Economy, Infrastructure, Logistics, Entity
from core.systems.settlement import SettlementSystem

def test_settlements():
    print("Initializing Test Database...")
    db_path = "test_settlement.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    registry = ECSRegistry(db_path)
    system = SettlementSystem(registry)
    
    # Create Settlement A (Wood Producer)
    entA = Entity("Forestburg")
    entA.add_component(Demographics(pop_total=500, growth_rate=0.01, culture="Human"))
    entA.add_component(Economy(wealth=200, primary_export="Wood", primary_import="Iron", tax_rate=0.1))
    entA.add_component(Logistics(resources={"Food": 200000, "Wood": 100}))
    registry.add_entity(entA)
    
    # Create Settlement B (Iron Producer)
    entB = Entity("Ironpeak")
    entB.add_component(Demographics(pop_total=300, growth_rate=0.01, culture="Dwarf"))
    entB.add_component(Economy(wealth=800, primary_export="Iron", primary_import="Wood", tax_rate=0.15))
    entB.add_component(Logistics(resources={"Food": 150000, "Iron": 50}))
    registry.add_entity(entB)
    
    print("\n[Initial State]")
    print(f" Forestburg: Pop {entA.get_component(Demographics).pop_total}, Wealth {entA.get_component(Economy).wealth}, Food {entA.get_component(Logistics).resources['Food']}, Wood {entA.get_component(Logistics).resources['Wood']}, Iron {entA.get_component(Logistics).resources.get('Iron', 0)}")
    print(f" Ironpeak:   Pop {entB.get_component(Demographics).pop_total}, Wealth {entB.get_component(Economy).wealth}, Food {entB.get_component(Logistics).resources['Food']}, Iron {entB.get_component(Logistics).resources['Iron']}, Wood {entB.get_component(Logistics).resources.get('Wood', 0)}")
    
    print("\n[Simulating 12 Months...]")
    for _ in range(12):
        system.process_tick()
        
    print("\n[Final State]")
    print(f" Forestburg: Pop {entA.get_component(Demographics).pop_total}, Wealth {entA.get_component(Economy).wealth}, Food {entA.get_component(Logistics).resources['Food']}, Wood {entA.get_component(Logistics).resources['Wood']}, Iron {entA.get_component(Logistics).resources.get('Iron', 0)}")
    print(f" Ironpeak:   Pop {entB.get_component(Demographics).pop_total}, Wealth {entB.get_component(Economy).wealth}, Food {entB.get_component(Logistics).resources['Food']}, Iron {entB.get_component(Logistics).resources['Iron']}, Wood {entB.get_component(Logistics).resources.get('Wood', 0)}")
    
    # Assertions
    assert entA.get_component(Demographics).pop_total > 500, "Population should have grown"
    assert entA.get_component(Logistics).resources.get('Iron', 0) > 0, "Forestburg should have imported Iron"
    assert entB.get_component(Logistics).resources.get('Wood', 0) > 0, "Ironpeak should have imported Wood"
    
    print("\nALL SETTLEMENT TESTS PASSED")
    
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_settlements()
