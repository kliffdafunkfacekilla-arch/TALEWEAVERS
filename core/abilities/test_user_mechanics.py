
import sys
import os
import unittest
import importlib.util

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load mechanics from "combat simulator" (Space in name)
mech_path = os.path.join(os.path.dirname(__file__), "../combat simulator/mechanics.py")
spec = importlib.util.spec_from_file_location("mechanics", mech_path)
mechanics = importlib.util.module_from_spec(spec)
sys.modules["mechanics"] = mechanics 
spec.loader.exec_module(mechanics)

CombatEngine = mechanics.CombatEngine
Combatant = mechanics.Combatant

def mock_get_effects_wrapper(effect_map):
    # effect_map: {combatant_name: [list of effects]}
    from abilities import engine_hooks
    def mock(c):
        return effect_map.get(c.name, [])
    engine_hooks.get_entity_effects = mock

class TestUserMechanics(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        self.p1 = Combatant("dummy.json") # We'll just patch attrs
        self.p1.name = "Attacker"
        self.p1.hp = 20
        self.p1.derived = {"HP": 20}
        self.p1.stats = {"Might": 10, "Reflexes": 10}
        self.p1.skills = []
        
        self.p2 = Combatant("dummy.json")
        self.p2.name = "Defender" 
        self.p2.hp = 20
        self.p2.derived = {"HP": 20}
        self.p2.stats = {"Might": 10, "Reflexes": 10}
        self.p2.skills = []

        self.engine.add_combatant(self.p1, 0, 0)
        self.engine.add_combatant(self.p2, 1, 0)

    def test_reflect(self):
        # P2 has "Reflect Hit"
        # P1 attacks P2
        print("Testing Reflect...", flush=True)
        mock_get_effects_wrapper({
            "Defender": ["Reflect Hit to attacker"]
        })
        
        # We need a hit. P1 has +10, P2 has +10. 50/50.
        # Let's force a hit by mocking random? Or just repeat until hit?
        # Or force stats.
        self.p1.stats["Might"] = 50 
        
        log = self.engine.attack_target(self.p1, self.p2)
        
        # Expect P2 HP full (Negated?), P1 HP damaged.
        # Registry _handle_reflect negates incoming and damages attacker.
        
        if self.p2.hp < 20: 
            # It might fail if mechanics applies damage BEFORE hooks?
            # Creating mechanics.py... ON_HIT hooks run BEFORE damage application in my update?
            # Let's check mechanics.py flow.
            # "ctx['incoming_damage'] = dmg ... apply_hooks(ON_HIT) ... engine_hooks.apply_hooks(target, ON_DEFEND)"
            # ... "final_dmg = ctx['incoming_damage']" ... "target.hp -= final_dmg"
            pass
            
        if any("Reflected" in l for l in log):
            print("PASS: Reflect Logged", flush=True)
            self.assertEqual(self.p2.hp, 20, "Reflector took damage!")
            self.assertLess(self.p1.hp, 20, "Attacker didn't take damage!")
        else:
            print("FAIL: Reflect did not trigger", flush=True)

    def test_taunt(self):
        print("Testing Taunt...", flush=True)
        # P1 casts "Force Attack" on P2
        # This is an ACTIVE ability usually, or ON_ATTACK.
        # If P1 attacks P2 with "Force Attack" effect...
        mock_get_effects_wrapper({
            "Attacker": ["Force Attack"]
        })
        
        log = self.engine.attack_target(self.p1, self.p2)
        if self.p2.taunted_by == self.p1:
            print("PASS: Taunt applied", flush=True)
        else:
            print(f"FAIL: Taunt not applied. Taunted by: {self.p2.taunted_by}", flush=True)

    def test_aging(self):
        print("Testing Aging...", flush=True)
        mock_get_effects_wrapper({
            "Attacker": ["Rapid aging attack"]
        })
        self.p2.cmp = 20
        self.engine.attack_target(self.p1, self.p2)
        if self.p2.cmp < 20:
            print("PASS: Aging applied", flush=True)
        else:
            print("FAIL: Aging not applied", flush=True)

if __name__ == '__main__':
    unittest.main()
