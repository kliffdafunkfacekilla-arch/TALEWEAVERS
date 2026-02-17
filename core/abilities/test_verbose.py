
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
from abilities.engine_hooks import get_entity_effects

class MockCombatant(Combatant):
    def __init__(self, name, hp=20):
        # Bypass file loading
        self.name = name
        self.species = "Human" # Default
        self.stats = {"Might": 10, "Reflexes": 10, "Endurance": 10}
        self.derived = {"HP": hp, "Speed": 30}
        self.skills = []
        self.traits = []
        self.powers = []
        self.inventory = []
        
        self.hp = hp
        self.max_hp = hp
        self.x = 0
        self.y = 0
        
        self.is_prone = False
        self.is_grappled = False
        self.is_blinded = False
        self.is_restrained = False
        self.is_stunned = False
        self.is_paralyzed = False
        self.is_poisoned = False
        self.is_frightened = False
        self.is_charmed = False
        self.is_deafened = False
        self.is_invisible = False

    def get_stat(self, name): return self.stats.get(name, 0)
    def get_skill_rank(self, name): return 0
    def is_alive(self): return self.hp > 0

class TestAbilities(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        self.p1 = MockCombatant("Attacker", hp=20)
        self.p2 = MockCombatant("Defender", hp=20)
        self.engine.add_combatant(self.p1, 0, 0)
        self.engine.add_combatant(self.p2, 1, 0) # Adjacent (5ft)

    def test_run_all(self):
        # BASIC DAMAGE
        print("Testing Basic Damage...", flush=True)
        self.run_with_mock(self.p1, ["Deal 5 Fire Damage"])
        log = self.engine.attack_target(self.p1, self.p2)
        if not any("Effect (Fire): 5 damage" in l for l in log):
            print("FAIL: Basic Damage Log missing", flush=True)
        else:
            print("PASS: Basic Damage", flush=True)
            
        # PUSH
        print("Testing Push...", flush=True)
        # Reset positions
        self.p1.x, self.p1.y = 0, 0
        self.p2.x, self.p2.y = 1, 0
        self.run_with_mock(self.p1, ["Push 10ft"])
        log = self.engine.attack_target(self.p1, self.p2)
        if self.p2.x != 3:
            print(f"FAIL: Push Position wrong. p2.x={self.p2.x}, expected 3", flush=True)
        else:
            print("PASS: Push", flush=True)

        # STATUS
        print("Testing Status...", flush=True)
        self.p2.is_stunned = False
        self.run_with_mock(self.p1, ["Target is Stunned"])
        log = self.engine.attack_target(self.p1, self.p2)
        if not self.p2.is_stunned:
             print("FAIL: Status Stunned not set", flush=True)
             print("LOG:", log, flush=True)
        else:
             print("PASS: Status", flush=True)

        # HEALING
        print("Testing Healing...", flush=True)
        self.p1.hp = 10
        self.run_with_mock(self.p1, ["Heal 5 HP"])
        self.engine.attack_target(self.p1, self.p2)
        if self.p1.hp <= 10:
            print(f"FAIL: Healing. hp={self.p1.hp}, expected > 10", flush=True)
        else:
            print(f"PASS: Healing (hp={self.p1.hp})", flush=True)

    def run_with_mock(self, combatant, effects):
        from abilities import engine_hooks
        def mock(c):
            if c == combatant: return effects
            return []
        engine_hooks.get_entity_effects = mock

if __name__ == '__main__':
    t = TestAbilities()
    t.setUp()
    t.test_run_all()
