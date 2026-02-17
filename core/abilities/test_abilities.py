
import sys
import os
import unittest
import importlib.util

# Add root to path
# Add root to path (Up 2 levels to Desktop/BRQSE)
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# Load mechanics from "combat simulator" (Space in name)
# Load mechanics from correct path
mech_path = os.path.join(os.path.dirname(__file__), "../combat/mechanics.py")
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
        self.team = "A" # Default team
        self.species = "Human" # Default
        self.status = {} # Initialize status dict
        self.active_effects = [] # Initialize active effects list
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        self.attacks_received_this_round = 0
        self.is_blessed = False
        self.is_hasted = False
        self.is_cursed = False
        self.is_staggered = False
        self.is_weakened = False
        self.is_slowed = False
        self.is_shaken = False # Added shaken
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
        self.is_shaken = False # Added shaken
        self._is_stunned = False 
        
        self.charmed_by = None
        
    @property
    def is_stunned(self): return self._is_stunned
    @is_stunned.setter
    def is_stunned(self, val): self._is_stunned = val
        
    def apply_effect(self, name, duration):
        # Mock application for testing
        print(f"DEBUG: Applying effect {name} to {self.name}")
        if name == "Stunned": self.is_stunned = True
        if name == "Prone": self.is_prone = True

    def get_stat(self, name): return self.stats.get(name, 0)
    
    def get_stat_modifier(self, stat):
        val = self.get_stat(stat)
        return (val - 10) // 2
        
    def get_skill_rank(self, name): return 0
    def is_alive(self): return self.hp > 0
    
    def has_attack_advantage(self):
        return self.is_blessed or self.is_hasted or self.is_invisible

    def has_attack_disadvantage(self):
         return (self.is_staggered or self.is_weakened or self.is_poisoned or 
                self.is_frightened or self.is_blinded or self.is_shaken)
    
    def is_attack_target_advantaged(self, attacker):
        # Simplified: If I am prone, they have adv
        return self.is_prone
        
    def is_attack_target_disadvantaged(self, attacker):
        return False


class TestAbilities(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        self.p1 = MockCombatant("Attacker", hp=20)
        self.p2 = MockCombatant("Defender", hp=20)
        self.p1.stats["Might"] = 100 # Ensure hit
        self.p1.stats["Finesse"] = 100
        self.p1.stats["Intuition"] = 100
        self.engine.add_combatant(self.p1, 0, 0)
        self.engine.add_combatant(self.p2, 1, 0) # Adjacent (5ft)

    def test_basic_damage(self):
        # Mock effects
        from abilities import engine_hooks
        original_get = engine_hooks.get_entity_effects
        
        def mock_get_effects(comb):
            print(f"DEBUG: Mock called for {comb.name}")
            if comb.name == "Attacker":
                return ["Deal 5 Fire Damage"]
            return []
        engine_hooks.get_entity_effects = mock_get_effects
        
        try:
            log = self.engine.attack_target(self.p1, self.p2)
            print("DEBUG LOG:", log) # DEBUG
            # Log format: "Effect deals 5 Fire damage!"
            # Log format: "Effect deals 5 Fire damage!"
            self.assertTrue(any("Effect deals 5 Fire damage" in l for l in log))
            self.assertLess(self.p2.hp, 20)
        finally:
            engine_hooks.get_entity_effects = original_get

    def test_push_effect(self):
        from abilities import engine_hooks
        original_get = engine_hooks.get_entity_effects
        
        def mock_get_effects(comb):
            if comb.name == "Attacker":
                return ["Push 10ft"] # Should be 2 squares
            return []
        engine_hooks.get_entity_effects = mock_get_effects
        
        try:
            # P1 at 0,0. P2 at 1,0.
            # Push 10ft (2 sq) -> P2 should end at 3,0? 
            # (Start 1,0 -> +2x -> 3,0)
            log = self.engine.attack_target(self.p1, self.p2)
            
            # Check log "is Pushed 10ft!"
            self.assertTrue(any("is Pushed 10ft!" in l for l in log))
            
            # Check Position (Engine mock might not move if simple? 
            # Mechanics.attack_target doesn't default apply movement unless integrated.
            # But the effect handler executed. Log check is sufficient for unit test of registry.)
        finally:
            engine_hooks.get_entity_effects = original_get

    def test_status_effect(self):
        from abilities import engine_hooks
        original_get = engine_hooks.get_entity_effects
        
        def mock_get_effects(comb):
            if comb.name == "Attacker":
                return ["Target is Stunned"] # Regex: r"Stun"
            return []
        engine_hooks.get_entity_effects = mock_get_effects
        
        try:
            log = self.engine.attack_target(self.p1, self.p2)
            # Log: "Defender Stunned for 1 round(s)!"
            self.assertTrue(any("Stunned for 1 round(s)!" in l for l in log))
            self.assertTrue(self.p2.is_stunned)
        finally:
            engine_hooks.get_entity_effects = original_get
            
    def test_healing(self):
         from abilities import engine_hooks
         original_get = engine_hooks.get_entity_effects
         
         def mock_get_effects(comb):
             if comb.name == "Attacker":
                 return ["Heal 5 HP"] 
             return []
         engine_hooks.get_entity_effects = mock_get_effects
         
         try:
             # Heal targets the target context (Defender) by default in combat
             self.p2.hp = 10 
             self.engine.attack_target(self.p1, self.p2)
             
             # Check p2 healed
             self.assertGreater(self.p2.hp, 10)
         finally:
             engine_hooks.get_entity_effects = original_get


if __name__ == '__main__':
    unittest.main()
