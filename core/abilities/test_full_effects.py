
import sys
import os
import importlib.util

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

mech_path = os.path.join(os.path.dirname(__file__), "../combat simulator/mechanics.py")
spec = importlib.util.spec_from_file_location("mechanics", mech_path)
mechanics = importlib.util.module_from_spec(spec)
sys.modules["mechanics"] = mechanics
spec.loader.exec_module(mechanics)

CombatEngine = mechanics.CombatEngine
Combatant = mechanics.Combatant

from abilities.effects_registry import registry

def test_aoe():
    print("=== Testing AOE ===", flush=True)
    engine = CombatEngine()
    
    caster = Combatant("dummy.json")
    caster.name = "Wizard"
    caster.stats = {"Might": 5}
    engine.add_combatant(caster, 5, 5)
    
    # Add enemies nearby
    for i, pos in enumerate([(6,5), (4,5), (5,6), (7,7)]):
        e = Combatant("dummy.json")
        e.name = f"Enemy{i+1}"
        e.hp = 10
        e.stats = {"Might": 2, "Reflexes": 2}
        engine.add_combatant(e, pos[0], pos[1])
    
    ctx = {"attacker": caster, "engine": engine, "log": []}
    registry.resolve("15ft radius explosion", ctx)
    print(f"AOE Targets: {[t.name for t in ctx.get('aoe_targets', [])]}")
    for line in ctx["log"]:
        print(line)

def test_charge():
    print("\n=== Testing Charge ===", flush=True)
    engine = CombatEngine()
    
    charger = Combatant("dummy.json")
    charger.name = "Knight"
    charger.stats = {"Might": 5}
    engine.add_combatant(charger, 0, 0)
    
    target = Combatant("dummy.json")
    target.name = "Goblin"
    target.hp = 15
    target.stats = {"Reflexes": 2}
    engine.add_combatant(target, 4, 0)
    
    print(f"Before: Knight at ({charger.x},{charger.y}), Goblin HP: {target.hp}")
    
    ctx = {"attacker": charger, "target": target, "engine": engine, "log": []}
    registry.resolve("Line Charge attack", ctx)
    
    for line in ctx["log"]:
        print(line)
    print(f"After: Knight at ({charger.x},{charger.y}), Goblin HP: {target.hp}")

def test_summon():
    print("\n=== Testing Summon ===", flush=True)
    engine = CombatEngine()
    
    caster = Combatant("dummy.json")
    caster.name = "Summoner"
    engine.add_combatant(caster, 5, 5)
    
    print(f"Combatants before: {len(engine.combatants)}")
    
    ctx = {"attacker": caster, "engine": engine, "log": []}
    registry.resolve("Summon a creature", ctx)
    
    for line in ctx["log"]:
        print(line)
    print(f"Combatants after: {len(engine.combatants)}")

def test_multihit():
    print("\n=== Testing Multi-hit ===", flush=True)
    engine = CombatEngine()
    
    attacker = Combatant("dummy.json")
    attacker.name = "Monk"
    attacker.stats = {"Might": 8}
    engine.add_combatant(attacker, 0, 0)
    
    target = Combatant("dummy.json")
    target.name = "Target"
    target.hp = 20
    target.stats = {"Reflexes": 5}
    engine.add_combatant(target, 1, 0)
    
    print(f"Target HP before: {target.hp}")
    
    ctx = {"attacker": attacker, "target": target, "engine": engine, "log": []}
    registry.resolve("Multi-hit attack (Low Dmg)", ctx)
    
    for line in ctx["log"]:
        print(line)
    print(f"Target HP after: {target.hp}")

if __name__ == "__main__":
    test_aoe()
    test_charge()
    test_summon()
    test_multihit()
    print("\n=== All Tests Complete ===")
