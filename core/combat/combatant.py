from typing import Optional, List, Dict, Tuple, Any
from models.character import Character
from core.stubs import Dice, StatusManager, Conditions, Stats

class Combatant:
    """
    Runtime wrapper for a Character in combat.
    Manages Position, Initiative, and tactical status (Elevation, Cover, Facing).
    """
    def __init__(self, character: Any, x: int = 0, y: int = 0, team: str = "Neutral"):
        self.character = character
        self.x = x
        self.y = y
        self.team = team
        self.initiative = 0
        
        # Tactical State
        self.elevation = 0
        self.is_behind_cover = False
        self.facing = "N" # N, S, E, W
        
        # Runtime Resource State
        self.hp = getattr(character, "current_hp", 30)
        self.max_hp_val = getattr(character, "max_hp", 30)
        self.sp = getattr(character, "current_stamina", 30)
        self.max_sp = getattr(character, "max_stamina", 30)
        self.cmp = getattr(character, "current_composure", 30)
        self.max_cmp = getattr(character, "max_composure", 30)
        self.fp = getattr(character, "current_focus", 30)
        self.max_fp = getattr(character, "max_focus", 30)
        
        # Action Economy
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        self.movement_max = getattr(character, "base_movement", 30)
        self.movement_remaining = self.movement_max

        self.status = StatusManager(self)
        self.is_dead = False
        self.is_broken = False
        self.is_exhausted = False
        self.is_drained = False
        
        # Armor Attribute Mapping
        self.armor_attr_map = {
            "Light": "Reflexes",
            "Medium": "Willpower",
            "Heavy": "Endurance",
            "Natural": "Vitality",
            "Cloth": "Knowledge",
            "Utility": "Intuition"
        }

    @property
    def name(self): return getattr(self.character, "name", "Unknown")
    @property
    def species(self): return getattr(self.character, "species", "Unknown")
    @property
    def sprite(self): return getattr(self.character, "sprite", "badger_front.png")

    @property
    def max_hp(self): return self.max_hp_val

    @property
    def skills(self): return getattr(self.character, "skills", [])
    @property
    def powers(self): return getattr(self.character, "powers", [])

    def reset_turn(self):
        self.action_used = False
        self.bonus_action_used = False
        self.movement_remaining = self.movement_max

    def get_stat(self, stat_name: str) -> int:
        if hasattr(self.character, "get_stat"):
             return self.character.get_stat(stat_name)
        stats = getattr(self.character, "stats", {})
        return stats.get(stat_name, 10)

    def get_stat_mod(self, stat_name: str) -> int:
        val = self.get_stat(stat_name)
        return (val - 10) // 2

    def get_skill_rank(self, skill_name: str) -> int:
        """Returns the character's rank in a specific skill."""
        skills = getattr(self.character, "skills", {})
        if isinstance(skills, dict):
            return skills.get(skill_name, 0)
        elif isinstance(skills, list):
            # If it's a list [Skill1, Skill2], rank is 1 if present
            return 1 if skill_name in skills else 0
        return 0

    def get_defense_info(self) -> Tuple[str, str]:
        """Returns (Stat_Name, Skill_Name) for defense roll."""
        # 1. Check for explicit armor_type override on character (useful for mocks)
        explicit_armor = getattr(self.character, "armor_type", None)
        if explicit_armor:
            return self.armor_attr_map.get(explicit_armor, "Reflexes"), explicit_armor

        # 2. Check inventory
        inventory = getattr(self.character, "inventory", None)
        if not inventory:
            return "Reflexes", "Light" # Default unarmored/light

        # 3. Check equipped armor
        # Handle both list-based and dict-based inventory
        armor_item = None
        if hasattr(inventory, "equipped"):
            armor_item = inventory.equipped.get("Armor")
        
        if not armor_item:
            return "Reflexes", "Light"

        # 4. Get armor family
        family = getattr(armor_item, "family", "Light")
        stat = self.armor_attr_map.get(family, "Reflexes")
        return stat, family

    def get_weapon_skill_name(self) -> str:
        """Returns the skill name for the currently equipped weapon."""
        inventory = getattr(self.character, "inventory", None)
        if not inventory:
            return "Simple" # Default/Unarmed

        # Handle both list/dict inventory
        weapon_item = None
        if hasattr(inventory, "equipped"):
            weapon_item = inventory.equipped.get("Main Hand")
        
        if not weapon_item:
            return "Simple"

        return getattr(weapon_item, "family", "Simple")

    def roll_initiative(self) -> int:
        intuit = self.get_stat("Intuition")
        reflex = self.get_stat("Reflexes")
        alertness = intuit + reflex
        roll, _, _ = Dice.roll("1d20")
        self.initiative = roll + alertness
        return self.initiative

    def take_damage(self, amount: int, damage_type: str = "Physical") -> int:
        actual = min(amount, self.hp)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
        return actual

    def take_social_damage(self, amount: int) -> int:
        actual = min(amount, self.cmp)
        self.cmp -= actual
        if self.cmp <= 0:
            self.cmp = 0
            self.is_broken = True
        return actual

    def add_condition(self, condition: str, duration: int = 1):
        self.status.add_condition(condition, duration)

    def tick_effects(self) -> List[str]:
        return self.status.tick()

    @property
    def is_alive(self) -> bool:
        return self.hp > 0 and not self.is_dead
