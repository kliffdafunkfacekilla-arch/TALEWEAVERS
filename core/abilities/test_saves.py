
import sys
import os
import importlib.util

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load mechanics
mech_path = os.path.join(os.path.dirname(__file__), "../combat simulator/mechanics.py")
spec = importlib.util.spec_from_file_location("mechanics", mech_path)
mechanics = importlib.util.module_from_spec(spec)
sys.modules["mechanics"] = mechanics
spec.loader.exec_module(mechanics)

CombatEngine = mechanics.CombatEngine
Combatant = mechanics.Combatant

def test_save_system():
    print("=== Testing Save System ===", flush=True)
    
    engine = CombatEngine()
    
    # Mock caster
    caster = Combatant("dummy.json")
    caster.name = "Wizard"
    caster.hp = 20
    caster.stats = {"Knowledge": 5, "Charm": 3}
    
    # Mock target
    target = Combatant("dummy.json")
    target.name = "Goblin"
    target.hp = 15
    target.stats = {"Willpower": 2, "Reflexes": 3}
    
    engine.add_combatant(caster, 0, 0)
    engine.add_combatant(target, 1, 0)
    
    # Test power
    power = {
        "Name": "Fear Spell",
        "Stat": "Charm",
        "Effect": "Target must save or be Frightened"
    }
    
    print(f"\nCaster: {caster.name} (Charm: {caster.stats['Charm']})")
    print(f"Target: {target.name} (Willpower: {target.stats['Willpower']})")
    print(f"Power: {power['Name']}")
    print("-" * 40)
    
    log = engine.cast_power(caster, target, power, save_type="Willpower")
    for line in log:
        print(line, flush=True)
    
    print(f"\nTarget is_frightened: {getattr(target, 'is_frightened', False)}")
    print("=== Test Complete ===", flush=True)

if __name__ == "__main__":
    test_save_system()
