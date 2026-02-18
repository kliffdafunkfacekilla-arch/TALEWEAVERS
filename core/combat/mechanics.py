
import json
import os
import random
import math
import sys
import time

# Add local directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Try to import Engines
try:
    from .ai_engine import AIDecisionEngine
except ImportError:
    AIDecisionEngine = None
    
try:
    from systems.inventory import Inventory
except ImportError:
    Inventory = None

try:
    from systems.progression import ProgressionEngine
except ImportError:
    ProgressionEngine = None
    print("[Mechanics] Warning: Could not import ProgressionEngine")

# Ensure we can import abilities module if it's in a subfolder relative to this script
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
try:
    from core.abilities import engine_hooks
except ImportError:
    from abilities import engine_hooks

try:
    try:
        from core.core.stubs import Stats, Conditions, StatusManager
    except ImportError:
        from core.stubs import Stats, Conditions, StatusManager
except ImportError as e:
    # Fallback to local placeholders if stubs missing
    class Conditions:
        STAGGERED = "Staggered"
    StatusManager = None
    print(f"[Mechanics] Warning: Could not import StatusManager: {e}")

# --- CONSTANTS ---
STAT_BLOCK = ["Might", "Reflexes", "Endurance", "Vitality", "Fortitude", "Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower", "Finesse"]

# --- TERRAIN DATA (synced with Data/Terrain_Types.csv) ---
TERRAIN_DATA = {
    "normal": {"move_cost": 1, "damage_type": None, "damage_dice": None},
    "difficult": {"move_cost": 2, "damage_type": None, "damage_dice": None},
    "water_shallow": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "fire_resistance"},
    "water_deep": {"move_cost": 3, "damage_type": None, "damage_dice": None, "effect": "swim_required"},
    "ice": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "slip_prone"},
    "mud": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "grapple_disadvantage"},
    "fire": {"move_cost": 2, "damage_type": "Fire", "damage_dice": "1d6"},
    "acid": {"move_cost": 2, "damage_type": "Acid", "damage_dice": "1d8"},
    "spikes": {"move_cost": 2, "damage_type": "Piercing", "damage_dice": "1d10"},
    "darkness": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "blinded"},
    "high_ground": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "ranged_advantage"},
    "tree": {"move_cost": 99, "damage_type": None, "damage_dice": None, "effect": "cover"},
    "rubble": {"move_cost": 2, "damage_type": None, "damage_dice": None},
    "tall_grass": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "half_cover_prone"},
    "lava": {"move_cost": 99, "damage_type": "Fire", "damage_dice": "4d10"},
    "pit": {"move_cost": 1, "damage_type": "Bludgeoning", "damage_dice": "2d6", "effect": "fall"},
}

# Cover levels: 0=None, 1=Half, 2=Full
COVER_NONE = 0
COVER_HALF = 1
COVER_FULL = 2

class Tile:
    def __init__(self, terrain_type="normal", x=0, y=0):
        self.terrain_type = terrain_type
        self.x = x
        self.y = y
        self.elevation = 0
        self.is_occupied = False
        self.occupant = None
        self.hazards = []


from .ecs_adapter import CombatEntity

class LegacyCombatant(CombatEntity):
    def __init__(self, filepath=None, data=None):
        self.filepath = filepath
        # Load Data
        if data:
            self.data = data
        else:
            self.data = self._load_data(filepath)
            
        # Initialize ECS Components (Name, Stats, Vitals, Inventory)
        super().__init__(name=self.data.get("Name", "Unknown"), data=self.data)
        
        self.species = self.data.get("Species", "Unknown")
        
        # The following properties (hp, sp, fp) are now handled by CombatEntity components via setters
        # We re-set them here to ensure any custom logic in _load_data is respected, 
        # but the storage is now in self.components[Vitals]
        
        # Skills: Maintain local cache for speed or move to Component?
        # For now, keep as attribute to avoid breaking get_skill_rank
        raw_skills = self.data.get("Skills", [])
        if isinstance(raw_skills, list):
            self.skills = {s: 1 for s in raw_skills}
        else:
            self.skills = raw_skills # Assume dict
            
        # Data Normalization: Traits (Ensure strings)
        raw_traits = self.data.get("Traits", [])
        self.traits = []
        for t in raw_traits:
            if isinstance(t, dict):
                val = t.get("Name") or t.get("name")
                if val: self.traits.append(val)
            elif isinstance(t, str):
                self.traits.append(t)

        # Data Normalization: Powers (Ensure strings)
        raw_powers = self.data.get("Powers", [])
        self.powers = []
        for p in raw_powers:
            if isinstance(p, dict):
                val = p.get("Name") or p.get("name")
                if val: self.powers.append(val)
            elif isinstance(p, str):
                self.powers.append(p)
        
        # Initialize Inventory Manager
        if Inventory:
            self.inventory = Inventory()
            inv_data = self.data.get("Inventory", [])
            if isinstance(inv_data, list):
                for item_entry in inv_data:
                    if isinstance(item_entry, dict):
                        self.inventory.equip(item_entry.get("Name", "Unknown"))
                    else:
                        self.inventory.equip(item_entry)
        else:
            self.inventory = None
            
        self.xp = self.data.get("XP", 0) # Load XP, default 0
        
        # STATUS MANAGER
        if StatusManager:
            self.status = StatusManager(self)
        else:
            self.status = None
            
        self.taunted_by = None
        self.taunted_by = None
        self.charmed_by = None # Reference to the entity that charmed this combatant
        self.active_effects = [] # For temporary combat effects (e.g. from spells)
        
        # FIX: Critical states
        self.is_dead = False          # True = permanently dead until revived
        
        # INVENTORY SYSTEM
        # self.inventory initialized above
        self.equipped_spells = [] # List of Spell objects

        self.ai = None # Placeholder for AI Logic
        
        # PROGRESSION SYSTEM (Auto-Unlock Talents)
        if ProgressionEngine:
            pe = ProgressionEngine()
            new_traits = pe.check_unlocks(self)
            if new_traits:
                # Log or just accept? mechanics doesn't log on init easily.
                # Just keeping them in self.traits is enough.
                pass
        
        # Status Flags Init
        self.is_broken = False        # True = CMP at 0 (mental break)
        self.is_exhausted = False     # True = SP at 0 (physical exhaustion)
        self.is_drained = False       # True = FP at 0 (focus depleted)
        
        # === SIMPLIFIED STATUS FLAGS (Advantage/Disadvantage System) ===
        # Tier 1: Action Modifiers
        self.is_staggered = False     # Disadvantage on ALL action rolls
        self.is_shaken = False        # Disadvantage on DEFENSE rolls only
        self.is_weakened = False      # Disadvantage on ATTACK rolls only
        self.is_blessed = False       # Advantage on ALL action rolls
        self.is_hasted = False        # Advantage + Double Speed + Extra Action
        
        # Tier 2: Movement Modifiers
        self.is_slowed = False        # Speed halved
        self.is_grappled = False      # Speed = 0, Disadvantage on Reflex
        self.is_restrained = False    # Speed = 0, Attacks vs you have Advantage
        self.is_prone = False         # Melee Adv, Ranged Dis
        
        # === USER'S 3-TIER CONDITION SYSTEM ===
        
        # TIER 1: DISRUPT (Minor debuffs, clear quickly)
        self.is_staggered = False     # Disadvantage on next action, clears after use
        self.is_shaken = False        # Disadvantage on Mental/Social, can't approach fear source
        self.is_sickened = False      # Disadvantage on Physical rolls (attacks, athletics, fortitude)
        # self.is_prone already exists above
        
        # TIER 2: STOP (Severe debuffs)
        self.is_blinded = False       # Disadvantage on everything, attacks vs you Advantage
        self.is_stunned = False       # Turn skipped, auto-fail clashes
        # self.is_restrained already exists above
        self.is_charmed = False       # Cannot attack charmer
        self.charmed_by = None        # Reference to the charmer
        
        # TIER 3: KILL (DoT / Death effects)
        self.is_bleeding = False      # Take 1d4 at start of turn
        self.is_burning = False       # Take 1d6 at start of turn
        self.is_doomed = False        # Cannot heal, instant death at 0 HP
        
        # Legacy/Additional
        self.is_paralyzed = False     # Cannot move or act, melee = auto-crit
        self.is_petrified = False     # Turned to stone
        self.is_poisoned = False      # Disadvantage + 1d4 damage per turn
        self.is_frightened = False    # Disadvantage, cannot approach source
        self.is_confused = False      # Random action each turn
        self.is_taunted = False       # Must attack taunter
        self.is_invisible = False     # Advantage on attacks, attacks vs you Disadvantage
        self.is_disarmed = False      # Cannot use equipped weapon
        
        # === TACTICAL COMBAT STATE ===
        self.facing = "N"                     # Facing direction: N/S/E/W
        self.attacks_received_this_round = 0  # Tracks attacks for multi-attacker disadvantage
        
        # Duration-based effects: list of {name, duration, on_expire}
        # duration = rounds remaining (-1 = permanent until cleared)
        self.active_effects = []
        
        # Resources
        # print(f"DEBUG: Combatant Init - Resources Start {self.name}")
        # Resources (Formula: Derived_Stats.csv)
        def get_score(name): return self.data.get("Stats", {}).get(name, 10) # default to 10 if missing
        
        self.max_hp = 10 + get_score("Might") + get_score("Reflexes") + get_score("Vitality")
        self.max_cmp = 10 + get_score("Willpower") + get_score("Logic") + get_score("Awareness")
        self.max_sp = get_score("Endurance") + get_score("Finesse") + get_score("Fortitude")
        # print(f"DEBUG: Max SP set to {self.max_sp}")
        self.max_fp = get_score("Knowledge") + get_score("Charm") + get_score("Intuition")

        # Override with JSON Derived if explicit override logic exists? 
        # User requested "formulas for calculations", implying we should trust formula.
        # But let's respect "Current" vs "Max". Max should be formula. 
        # If JSON has higher/custom Max, that's tricky. For now, Formula is source of truth.
        
        self.hp = self.max_hp # Reset to max on load? Or load current?
        # Typically we load current. But for this simulation, we reset.
        
        self.cmp = self.max_cmp
        
        # Loadout & Net Pools
        self.sp_reserved = 0
        self.fp_reserved = 0
        self.sp_net_max = self.max_sp
        self.fp_net_max = self.max_fp
        
        self.sp = self.sp_net_max
        self.fp = self.fp_net_max
        
        # Speed: Vitality + Willpower -> Round UP to nearest 5
        # Formula: ceil((Vitality + Willpower) / 5) * 5
        try:
            vit = get_score("Vitality")
            will = get_score("Willpower")
            raw_spd = vit + will
            # Round up to nearest 5
            self.base_movement = math.ceil(raw_spd / 5) * 5
        except:
            self.base_movement = 30 # Default fallback
            
        if self.base_movement < 5: self.base_movement = 5
        self.movement = self.base_movement
        self.movement_remaining = self.movement
        
        # Action Economy Flags
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        
        # Position
        self.x = 0
        self.y = 0
        self.initiative = 0
        self.team = "Neutral" # Default team
        
        # TACTICAL PROPS (Required by GameLoop)
        self.elevation = 0
        self.is_behind_cover = False
        
        self._init_loadout()
        
    def _init_loadout(self):
        """Auto-equip items from data if Inventory exists"""
        if not self.inventory: return

        gear_items = []

        def collect(key):
            val = self.data.get(key)
            if isinstance(val, list):
                gear_items.extend(val)
            elif isinstance(val, dict):
                for v in val.values():
                    if v: gear_items.append(v)
            elif isinstance(val, str):
                gear_items.append(val)

        collect("Inventory")
        collect("Gear")
        collect("Weapons")
        collect("Armor")
        collect("Equipment")

        for item_entry in gear_items:
            name = item_entry
            if isinstance(item_entry, dict):
                name = item_entry.get("Name", "Unknown")

            if name and isinstance(name, str):
                self.inventory.equip(name)

        self.recalc_loadout()

    def recalc_loadout(self):
        """Calculates Reserved SP/FP/CMP from Gear/Spells and updates Net Pools."""
        # 1. Gear Loadout (SP)
        if self.inventory and hasattr(self.inventory, "get_loadout_cost"):
             self.sp_reserved = self.inventory.get_loadout_cost()
        else:
             self.sp_reserved = 0

        # 2. Spell Loadout (FP)
        self.fp_reserved = sum(getattr(s, "loadout_cost", 0) for s in self.equipped_spells)
        
        # 3. Curse Loadout (CMP)
        self.cmp_reserved = 0
        if hasattr(self, "inventory") and self.inventory:
            # Handle List[Dict] (JSON)
            if isinstance(self.inventory, list):
                 for item in self.inventory:
                     if isinstance(item, dict) and item.get("is_cursed"):
                         self.cmp_reserved += item.get("cmp_cost", 0)
            # Handle InventoryManager (Object)
            elif hasattr(self.inventory, "items"): 
                 for item in self.inventory.items:
                     if hasattr(item, "is_cursed") and item.is_cursed:
                         self.cmp_reserved += getattr(item, "cmp_cost", 0)

        # 4. Update Net Max
        self.sp_net_max = max(0, self.max_sp - self.sp_reserved)
        self.fp_net_max = max(0, self.max_fp - self.fp_reserved)
        self.cmp_net_max = max(0, self.max_cmp - self.cmp_reserved)

        # 5. Cap current if greater
        if self.sp > self.sp_net_max: self.sp = self.sp_net_max
        if self.fp > self.fp_net_max: self.fp = self.fp_net_max
        if getattr(self, "cmp", 0) > self.cmp_net_max: self.cmp = self.cmp_net_max

    def _load_data(self, filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: return {}

    def save_state(self):
        """Saves current stats/skills/xp back to the JSON file."""
        if not self.filepath: return
        
        # Update internal data dict structure
        self.data["Stats"] = self.stats
        self.data["Skills"] = self.skills
        self.data["Traits"] = self.traits
        self.data["XP"] = self.xp
        # Derived stats usually don't need saving if they are calc'd on load, 
        # but if you have permanent modifiers, save them here.
        
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=4)
            print(f"Character saved: {self.filepath}")
        except Exception as e:
            print(f"Error saving character: {e}")

    def roll_initiative(self):
        # Alertness = Intuition + Reflexes
        intuit = self.get_stat("Intuition")
        reflex = self.get_stat("Reflexes")
        alertness = intuit + reflex
        
        # BURT'S UPDATE: Check for Talent Flags
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        
        roll = roll1
        if getattr(self, "initiative_advantage", False):
            roll = max(roll1, roll2)
            
        bonus = getattr(self, "initiative_bonus", 0)
        
        self.initiative = roll + alertness + bonus
        return self.initiative

    def get_attack_range(self):
        """
        Calculates range based on equipped weapon + tags.
        """
        base_range = 5 # Default melee
        
        # Check equipped weapon tags (assuming you have an 'equipped_weapon' dict or object)
        # If your system is simple, maybe it's just in self.weapon_data
        
        # Mock weapon data access if not present
        wep = getattr(self, "weapon_data", {})
        tags = wep.get("tags", set())
        
        # Handle "Reach"
        if "Reach" in tags:
            base_range += 5
            
        # Handle "Thrown" (if we are throwing it)
        # For simplicity, if it has 'Thrown', we use the thrown range provided in data
        # or default to 30ft.
        if "Thrown" in tags:
            base_range = max(base_range, 30) 
            
        return base_range

    def get_stat(self, stat_name):
        return self.stats.get(stat_name, 10) # Default to 10 (Mod +0)

    def get_stat_modifier(self, stat_name):
        """
        Returns D&D 5e style modifier: (Score - 10) // 2
        e.g. 10 -> +0, 12 -> +1, 16 -> +3, 8 -> -1
        """
        score = self.get_stat(stat_name)
        return (score - 10) // 2

    def get_skill_rank(self, skill_name):
        return self.skills.get(skill_name, 0)
    
    # === ADVANTAGE/DISADVANTAGE ROLL SYSTEM ===
    
    def roll_with_advantage(self, has_advantage=False, has_disadvantage=False):
        """
        Roll d20 with advantage/disadvantage.
        Advantage: Roll 2d20, take higher.
        Disadvantage: Roll 2d20, take lower.
        If both: They cancel out, roll normally.
        """
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        
        if has_advantage and has_disadvantage:
            return roll1  # Cancel out
        elif has_advantage:
            return max(roll1, roll2)
        elif has_disadvantage:
            return min(roll1, roll2)
        else:
            return roll1
    
    def has_attack_advantage(self):
        """Returns True if this combatant has advantage on attacks."""
        return self.is_blessed or self.is_hasted or self.is_invisible
    
    def has_attack_disadvantage(self):
        """Returns True if this combatant has disadvantage on attacks."""
        return (self.is_staggered or self.is_weakened or self.is_poisoned or 
                self.is_frightened or self.is_blinded)
    
    def has_defense_advantage(self):
        """Returns True if this combatant has advantage on defense."""
        return self.is_blessed or self.is_hasted
    
    def has_defense_disadvantage(self):
        """Returns True if this combatant has disadvantage on defense."""
        return self.is_staggered or self.is_shaken
    
    def is_attack_target_advantaged(self, attacker):
        """Returns True if attacks against this combatant have advantage."""
        return (self.is_stunned or self.is_restrained or self.is_blinded or 
                self.is_paralyzed or attacker.is_invisible)
    
    def is_attack_target_disadvantaged(self, attacker):
        """Returns True if attacks against this combatant have disadvantage."""
        return self.is_invisible
    
    def get_effective_speed(self):
        """Returns current speed considering status effects."""
        if self.is_grappled or self.is_restrained or self.is_stunned or self.is_paralyzed:
            return 0
        speed = self.base_movement
        if self.is_hasted:
            speed *= 2
        if self.is_slowed:
            speed //= 2
        return max(speed, 0)
        

    def take_damage(self, amount, damage_type="Physical"):
        """Applies damage and returns True if dead."""
        self.hp -= amount
        if self.hp < 0: self.hp = 0
        return self.hp == 0 

    def is_alive(self):
        return self.hp > 0 and not self.is_dead
    
    def heal(self, amount):
        """
        Heal HP. FIX: Cannot heal if dead.
        Returns actual healing applied.
        """
        if self.is_dead:
            return 0  # Need resurrection, not healing
        
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp
    
    def revive(self, hp_amount=1):
        """
        Revive a dead character.
        """
        if self.is_dead:
            self.is_dead = False
            self.hp = min(hp_amount, self.max_hp)
            return True
        return False
    
    def check_resources(self):
        """
        Check resource levels and set broken states.
        Call this after modifying CMP/SP/FP.
        """
        # CMP = Mental break
        if self.cmp <= 0:
            self.cmp = 0
            self.is_broken = True
        elif self.cmp > 0:
            self.is_broken = False
            
        # SP = Exhaustion
        if self.sp <= 0:
            self.sp = 0
            self.is_exhausted = True
        elif self.sp > 0:
            self.is_exhausted = False
            
        # FP = Drained
        if self.fp <= 0:
            self.fp = 0
            self.is_drained = True
        elif self.fp > 0:
            self.is_drained = False

    def roll_save(self, save_type):
        """
        Roll a saving throw.
        save_type: 'Endurance' (tank), 'Reflex' (dodge), 'Fortitude' (resist), 
                   'Willpower' (mental), 'Intuition' (see through)
        Returns: (roll_total, roll_natural)
        """
        stat_map = {
            "Endurance": "Endurance",
            "Reflex": "Reflexes",
            "Fortitude": "Fortitude",
            "Willpower": "Willpower",
            "Intuition": "Intuition"
        }
        stat = stat_map.get(save_type, save_type)
        nat_roll = random.randint(1, 20)
        mod = self.get_stat_modifier(stat)
        return nat_roll + mod, nat_roll

    # --- PROPERTIES FOR BACKWARD COMPATIBILITY ---
    def _get_status(self, condition):
        return self.status.has(condition) if self.status else False
    def _set_status(self, condition, val):
        if self.status:
            if val: self.status.add_condition(condition)
            else: self.status.remove_condition(condition)

    @property
    def is_prone(self): return self._get_status(Conditions.PRONE)
    @is_prone.setter
    def is_prone(self, val): self._set_status(Conditions.PRONE, val)

    @property
    def is_grappled(self): return self._get_status(Conditions.GRAPPLED)
    @is_grappled.setter
    def is_grappled(self, val): self._set_status(Conditions.GRAPPLED, val)

    @property
    def is_blinded(self): return self._get_status(Conditions.BLINDED)
    @is_blinded.setter
    def is_blinded(self, val): self._set_status(Conditions.BLINDED, val)

    @property
    def is_restrained(self): return self._get_status(Conditions.RESTRAINED)
    @is_restrained.setter
    def is_restrained(self, val): self._set_status(Conditions.RESTRAINED, val)

    @property
    def is_stunned(self): return self._get_status(Conditions.STUNNED)
    @is_stunned.setter
    def is_stunned(self, val): self._set_status(Conditions.STUNNED, val)

    @property
    def is_paralyzed(self): return self._get_status(Conditions.PARALYZED)
    @is_paralyzed.setter
    def is_paralyzed(self, val): self._set_status(Conditions.PARALYZED, val)

    @property
    def is_poisoned(self): return self._get_status(Conditions.POISONED)
    @is_poisoned.setter
    def is_poisoned(self, val): self._set_status(Conditions.POISONED, val)

    @property
    def is_frightened(self): return self._get_status(Conditions.FRIGHTENED)
    @is_frightened.setter
    def is_frightened(self, val): self._set_status(Conditions.FRIGHTENED, val)

    @property
    def is_charmed(self): return self._get_status(Conditions.CHARMED)
    @is_charmed.setter
    def is_charmed(self, val): self._set_status(Conditions.CHARMED, val)

    @property
    def is_deafened(self): return self._get_status(Conditions.DEAFENED)
    @is_deafened.setter
    def is_deafened(self, val): self._set_status(Conditions.DEAFENED, val)

    @property
    def is_invisible(self): return self._get_status(Conditions.INVISIBLE)
    @is_invisible.setter
    def is_invisible(self, val): self._set_status(Conditions.INVISIBLE, val)

    @property
    def is_confused(self): return self._get_status(Conditions.CONFUSED)
    @is_confused.setter
    def is_confused(self, val): self._set_status(Conditions.CONFUSED, val)

    @property
    def is_berserk(self): return self._get_status(Conditions.BERSERK)
    @is_berserk.setter
    def is_berserk(self, val): self._set_status(Conditions.BERSERK, val)
    
    @property
    def is_staggered(self): return self._get_status(Conditions.STAGGERED)
    @is_staggered.setter
    def is_staggered(self, val): self._set_status(Conditions.STAGGERED, val)

    @property
    def is_burning(self): return self._get_status(Conditions.BURNING)
    @is_burning.setter
    def is_burning(self, val): self._set_status(Conditions.BURNING, val)

    @property
    def is_bleeding(self): return self._get_status(Conditions.BLEEDING)
    @is_bleeding.setter
    def is_bleeding(self, val): self._set_status(Conditions.BLEEDING, val)

    @property
    def is_frozen(self): return self._get_status(Conditions.FROZEN)
    @is_frozen.setter
    def is_frozen(self, val): self._set_status(Conditions.FROZEN, val)

    @property
    def is_sanctuary(self): return self._get_status(Conditions.SANCTUARY)
    @is_sanctuary.setter
    def is_sanctuary(self, val): self._set_status(Conditions.SANCTUARY, val)


    def apply_effect(self, effect_name, duration=1, on_expire=None):
        """
        Apply a timed effect via StatusManager.
        """
        if self.status:
            self.status.add_timed_effect(effect_name, duration, on_expire)

    def tick_effects(self):
        """
        Delegates to StatusManager.tick()
        """
        if self.status:
            return self.status.tick()
        return []

class CombatEngine:
    def __init__(self, cols=12, rows=12):
        self.combatants = []
        self.turn_order = []
        self.current_turn_index = 0
        self.round_counter = 1
        
        # Map
        self.cols = cols
        self.rows = rows
        self.walls = set()
        self.hazards = []
        self.aoe_templates = []
        self.replay_log = []
        self.pending_world_updates = [] # Buffer for world changes (walls, hazards)
        
        # Tile Grid (for terrain and cover)
        self.tiles = [[Tile("normal", x, y) for x in range(cols)] for y in range(rows)]
        
        # Initialize AI Engine immediately if available
        self.ai = AIDecisionEngine() if AIDecisionEngine else None 
        self.log_callback = None
        
        # Clash State
        self.clash_active = False
        self.clash_participants = (None, None)
        self.clash_stat = None
        
    def attack_target(self, attacker, target):
        """
        Resolves an attack using Margin-Based Resolution (Combat_Formula.csv).
        Returns a list of log strings.
        """
        logs = []
        
        # 1. Roll to Hit
        # Uses Finesse (or Weapon Stat) vs Reflexes (Defense)
        atk_stat = "Finesse" # Default melee
        def_stat = "Reflexes"
        
        atk_mod = attacker.get_stat_modifier(atk_stat)
        def_mod = target.get_stat_modifier(def_stat)
        
        # Roll d20 + mod
        atk_roll = random.randint(1, 20)
        total_atk = atk_roll + atk_mod
        
        # Defense Roll (Active Defense)
        def_roll = random.randint(1, 20)
        total_def = def_roll + def_mod
        
        margin = total_atk - total_def
        
        logs.append(f"{attacker.name} attacks! (Atk {total_atk} vs Def {total_def}) Margin: {margin}")
        
        # --- MARGIN RESOLUTION TABLE ---
        
        # [BANTER HOOK]
        banter = getattr(self, "banter_engine", None)
        
        # Nat 20 = CRITICAL (Always hits, max margin effect)
        if atk_roll == 20:
            margin = max(margin, 10) # Ensure at least Smash
            logs.append("CRITICAL HIT!")
            if banter:
                line = banter.check_banter(attacker, "ON_HIT", 0.7)
                if line: logs.append(line)
        
        # Nat 1 = DISASTER
        if atk_roll == 1:
            attacker.take_damage(random.randint(1, 4))
            # attacker.is_prone = True # If supported
            logs.append("DISASTER! Attacker takes 1d4 self-damage.")
            if banter:
                line = banter.check_banter(attacker, "ON_DISASTER", 0.8)
                if line: logs.append(line)
            return logs

        # [WHISPER HOOK]
        whisper = getattr(self, "whisper_engine", None)

        if margin >= 10:
            # SMASH (+10 or more)
            dmg_roll = random.randint(1, 6) # Base Weapon Damage
            dmg_mod = attacker.get_stat_modifier("Might")
            total_dmg = max(1, dmg_roll + dmg_mod)
            target.take_damage(total_dmg)
            logs.append(f"SMASH! {target.name} takes {total_dmg} dmg.")
            if banter:
                line = banter.check_banter(target, "ON_DAMAGED", 0.5)
                if line: logs.append(line)
            if whisper:
                logs.extend(whisper.process_event(attacker, "ON_DAMAGE", f"smashed {target.name}"))
            
        elif margin >= 6:
            # SOLID HIT (+6 to +9)
            dmg_roll = random.randint(1, 6)
            dmg_mod = attacker.get_stat_modifier("Might")
            total_dmg = max(1, dmg_roll + dmg_mod)
            target.take_damage(total_dmg)
            logs.append(f"SOLID HIT! {target.name} takes {total_dmg} dmg.")
            if banter:
                line = banter.check_banter(target, "ON_DAMAGED", 0.3)
                if line: logs.append(line)
            if whisper:
                logs.extend(whisper.process_event(attacker, "ON_DAMAGE", f"struck {target.name}"))
            
        elif margin >= 1:
            # GRAZE (+1 to +5) -> CMP Damage (Stress)
            stress_dmg = random.randint(1, 6)
            if hasattr(target, "take_social_damage"):
                 target.take_social_damage(stress_dmg)
            elif hasattr(target, "cmp"):
                 target.cmp = max(0, target.cmp - stress_dmg)
            
            logs.append(f"GRAZE! {target.name} takes {stress_dmg} Composure dmg (Stress).")
            
        elif margin == 0:
            # THE CLASH (Tie)
            self.clash_active = True
            self.clash_participants = (attacker, target)
            self.clash_stat = atk_stat # Or context dependent
            logs.append("THE CLASH! Weapons lock. Initiate Clash Protocol.")
            
        elif margin <= -7:
            # HARD DEFLECT (-7 or worse)
            # Attacker Staggered
            attacker.is_staggered = True
            logs.append("HARD DEFLECT! Attacker is Staggered.")
            if banter: 
                line = banter.check_banter(target, "ON_MISS", 0.6) # Target taunts!
                if line: logs.append(line)
            
        else:
            # MISS (-1 to -6)
            logs.append(f"MISS! {target.name} dodges.")
            if banter: 
                 line = banter.check_banter(target, "ON_MISS", 0.4)
                 if line: logs.append(line)
            
        if target.hp <= 0:
            logs.append(f"{target.name} collapses!")
            if banter:
                line = banter.check_banter(target, "ON_DEATH", 1.0)
                if line: logs.append(line)
            if whisper:
                logs.extend(whisper.process_event(attacker, "ON_KILL", f"slaughtered {target.name}"))
            
        return logs

    def resolve_clash(self, choice_a, choice_b=None):
        """
        Resolves a locking of weapons.
        choice_a: Attacker's Strategy (Press/Disengage)
        """
        if not self.clash_active: return ["No Clash Active."]
        
        attacker, defender = self.clash_participants
        if not attacker or not defender: return ["Invalid Clash State."]
        
        # Simple Resolution for now (Random Winner)
        # TODO: Implement full specific Clash Physics from Strat A vs Strat B
        logs = [f"Clash Resolution: {attacker.name} ({choice_a})"]
        
        winner = random.choice([attacker, defender])
        logs.append(f"{winner.name} wins the Clash!")
        
        self.clash_active = False
        self.clash_participants = (None, None)
        return logs
    
    # === TERRAIN & TILE METHODS ===
    
    def get_tile(self, x, y):
        """Get the Tile object at coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.tiles[y][x]
        return None
    
    def set_terrain(self, x, y, terrain_type):
        """Set terrain type at coordinates."""
        tile = self.get_tile(x, y)
        if tile:
            tile.terrain = terrain_type
            data = TERRAIN_DATA.get(terrain_type, TERRAIN_DATA["normal"])
            tile.move_cost = data.get("move_cost", 1)
            tile.damage_type = data.get("damage_type")
            tile.damage_dice = data.get("damage_dice")
            tile.effect = data.get("effect")
    
    def set_cover(self, x, y, direction, level):
        """Set cover on a tile edge. Direction: N/S/E/W. Level: 0=None, 1=Half, 2=Full."""
        tile = self.get_tile(x, y)
        if tile:
            if direction == "N": tile.cover_north = level
            elif direction == "S": tile.cover_south = level
            elif direction == "E": tile.cover_east = level
            elif direction == "W": tile.cover_west = level
    
    # === TACTICAL CHECKS (REVISED) ===
    
    def is_behind(self, attacker, target):
        """Returns True if attacker is in target's rear arc (180° behind facing)."""
        dx = attacker.x - target.x
        dy = attacker.y - target.y
        
        facing = getattr(target, 'facing', 'N')
        
        # Check if attacker is in rear arc based on target's facing
        if facing == "N" and dy > 0: return True   # Target faces N, attacker is South
        if facing == "S" and dy < 0: return True   # Target faces S, attacker is North
        if facing == "E" and dx < 0: return True   # Target faces E, attacker is West
        if facing == "W" and dx > 0: return True   # Target faces W, attacker is East
        return False
    
    def has_line_of_sight(self, attacker, target):
        """Returns True if clear LOS, False if blocked by walls or full cover."""
        x0, y0 = attacker.x, attacker.y
        x1, y1 = target.x, target.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while (x0, y0) != (x1, y1):
            # Skip attacker's tile
            if (x0, y0) != (attacker.x, attacker.y):
                # Check for wall
                if (x0, y0) in self.walls:
                    return False
                # Check for full cover tile
                tile = self.get_tile(x0, y0)
                if tile and tile.occupant and tile.occupant != target:
                    # Entity blocking? Optional: treat as half cover instead
                    pass
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        
        return True
    
    def get_cover_between(self, attacker, target):
        """Returns cover level (0=None, 1=Half, 2=Full) that target has from attacker."""
        # First check LOS
        if not self.has_line_of_sight(attacker, target):
            return COVER_FULL  # No LOS = Full Cover
        
        tile = self.get_tile(target.x, target.y)
        if not tile:
            return COVER_NONE
        
        # Determine attack direction
        dx = target.x - attacker.x
        dy = target.y - attacker.y
        
        # Get directional cover
        if abs(dx) >= abs(dy):
            if dx > 0:
                cover = tile.cover_west
            else:
                cover = tile.cover_east
        else:
            if dy > 0:
                cover = tile.cover_north
            else:
                cover = tile.cover_south
        
        # Cap at COVER_FULL (2) - no 3/4 cover
        return min(cover, COVER_FULL)
    
    def has_high_ground(self, attacker, target):
        """Returns True if attacker has high ground (elevation advantage)."""
        atk_tile = self.get_tile(attacker.x, attacker.y)
        tgt_tile = self.get_tile(target.x, target.y)
        
        if atk_tile and atk_tile.effect == "ranged_bonus":
            if tgt_tile and tgt_tile.effect != "ranged_bonus":
                return True
        return False
    
    def count_adjacent_enemies(self, target):
        """Returns count of enemies adjacent to target."""
        count = 0
        for c in self.combatants:
            if c.team != target.team and c.is_alive():
                if abs(c.x - target.x) <= 1 and abs(c.y - target.y) <= 1:
                    if c != target:
                        count += 1
        return count
        

        return False
        

    def create_wall(self, x, y):
        """Creates a wall at the specified coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.walls.add((x, y))
            
    def tick_hazards(self):
        """
        Call this at end of round to clean up expired zones.
        """
        active = []
        for h in self.hazards:
            h["duration"] -= 1
            if h["duration"] > 0:
                active.append(h)
        self.hazards = active

    def log(self, message):
        """Logs a message using the callback if available."""
        if self.log_callback:
            self.log_callback(message)
        
        self.clash_active = False
        self.clash_participants = (None, None) 
        self.clash_stat = None
        self.weapon_db = self._load_weapon_db()
        self.ai = AIDecisionEngine() if AIDecisionEngine else None

    def _load_weapon_db(self):
        db = {}
        # Path relative to brqse_engine/combat/mechanics.py -> ../../Data
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Data/weapons_and_armor.csv")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                header = f.readline()
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < 7: continue
                    name = parts[0]
                    tags = parts[6]
                    dice = "1d4"
                    if "DMG:" in tags:
                        for t in tags.split('|'):
                            if t.startswith("DMG:"):
                                sub = t.split(':')
                                if len(sub) > 1: dice = sub[1]
                                break
                    db[name] = dice
        except: pass
        return db
        # 3. Get Weapon/Armor skill modifiers
        weapon_skill = attacker.get_weapon_skill() if hasattr(attacker, 'get_weapon_skill') else 0
        armor_skill = target.get_armor_skill() if hasattr(target, 'get_armor_skill') else 0
        
        # 4. CONTESTED ROLLS
        # ATTACK: d20 + Weapon Skill + Attack Stat
        attack_roll = random.randint(1, 20)
        attack_bonus = attacker.get_stat(attack_stat) + weapon_skill
        attack_total = attack_roll + attack_bonus
        
        # DEFENSE: d20 + Armor Skill + Defense Stat (Reflexes)
        defense_roll = random.randint(1, 20)
        defense_stat = "Reflexes"  # Default defense stat
        defense_bonus = target.get_stat(defense_stat) + armor_skill
        defense_total = defense_roll + defense_bonus
        
        log.append(f"[ATTACK] {attacker.name}: {attack_roll}+{attack_bonus}={attack_total}")
        log.append(f"[DEFENSE] {target.name}: {defense_roll}+{defense_bonus}={defense_total}")
        
        # 5. RESOLVE CONTEST
        if attack_total > defense_total:
            # HIT - Calculate damage
            dmg_die = wep.get("damage_dice", 6) if wep else 6
            dmg = random.randint(1, dmg_die) + attacker.get_stat(attack_stat)
            target.take_damage(dmg)
            log.append(f"HIT! {attacker.name} deals {dmg} damage to {target.name}!")
            
            # Log for replay
            self.replay_log.append({
                "type": "attack",
                "actor": attacker.name,
                "target": target.name,
                "result": "hit",
                "damage": dmg,
                "attack_roll": attack_total,
                "defense_roll": defense_total,
                "target_hp": target.hp
            })
            
        elif attack_total < defense_total:
            # MISS
            log.append(f"MISS! {target.name} deflects the attack!")
            self.replay_log.append({
                "type": "attack",
                "actor": attacker.name,
                "target": target.name,
                "result": "miss",
                "damage": 0,
                "attack_roll": attack_total,
                "defense_roll": defense_total
            })
            
        else:
            # TIE = PHYSICAL CLASH!
            log.append(f"CLASH! Rolls tied at {attack_total}!")
            clash_log = self.resolve_physical_clash(attacker, target, attack_stat)
            log.extend(clash_log)
        
        return log
    
    def resolve_physical_clash(self, attacker, target, stat_used):
        """
        Physical Clash triggered on tied attack/defense rolls.
        Both re-roll d20 + Stat. Winner executes a Technique, Loser is Staggered.
        """
        log = []
        log.append(f"=== PHYSICAL CLASH ({stat_used}) ===")
        
        # Clash Roll: d20 + Stat
        attacker_roll = random.randint(1, 20) + attacker.get_stat(stat_used)
        defender_roll = random.randint(1, 20) + target.get_stat(stat_used)
        
        log.append(f"{attacker.name} clashes: {attacker_roll}")
        log.append(f"{target.name} clashes: {defender_roll}")
        
        # Determine winner
        if attacker_roll > defender_roll:
            winner, loser = attacker, target
        elif defender_roll > attacker_roll:
            winner, loser = target, attacker
        else:
            # Double tie = both staggered, no technique
            attacker.is_staggered = True
            target.is_staggered = True
            log.append("DOUBLE TIE! Both combatants are STAGGERED!")
            return log
        
        # Loser is STAGGERED
        loser.is_staggered = True
        log.append(f"{loser.name} is STAGGERED! (Disadvantage next action)")
        
        # Winner executes TECHNIQUE based on stat
        technique = self.execute_clash_technique(winner, loser, stat_used)
        log.append(technique)
        
        # Log clash for replay
        self.replay_log.append({
            "type": "clash",
            "actor": winner.name,
            "target": loser.name,
            "stat": stat_used,
            "description": technique
        })
        
        return log
    
    def execute_clash_technique(self, winner, loser, stat):
        """Execute technique based on stat used in clash."""
        stat_upper = stat.upper() if stat else "MIGHT"
        
        if stat_upper == "MIGHT":
            # PRESS: Push target 5ft back, take their space
            old_x, old_y = loser.x, loser.y
            dir_x = 1 if loser.x > winner.x else (-1 if loser.x < winner.x else 0)
            dir_y = 1 if loser.y > winner.y else (-1 if loser.y < winner.y else 0)
            loser.x = max(0, min(self.cols - 1, loser.x + dir_x))
            loser.y = max(0, min(self.rows - 1, loser.y + dir_y))
            winner.x, winner.y = old_x, old_y
            return f"PRESS! {winner.name} pushes {loser.name} back and takes their position!"
            
        elif stat_upper in ["FINESSE", "REFLEXES"]:
            # TACTIC: Disarm target
            loser.is_disarmed = True
            return f"TACTIC! {winner.name} disarms {loser.name}!"
            
        elif stat_upper == "FORTITUDE":
            # DISENGAGE: Winner moves 5ft back freely
            dir_x = -1 if loser.x > winner.x else (1 if loser.x < winner.x else 0)
            dir_y = -1 if loser.y > winner.y else (1 if loser.y < winner.y else 0)
            winner.x = max(0, min(self.cols - 1, winner.x + dir_x))
            winner.y = max(0, min(self.rows - 1, winner.y + dir_y))
            return f"DISENGAGE! {winner.name} retreats safely!"
            
        elif stat_upper == "LOGIC":
            # MANEUVER: Move to target's side/back
            # Move to position behind loser
            behind_x = loser.x + (1 if loser.x > winner.x else -1)
            behind_y = loser.y
            winner.x = max(0, min(self.cols - 1, behind_x))
            winner.y = max(0, min(self.rows - 1, behind_y))
            return f"MANEUVER! {winner.name} flanks {loser.name}!"
            
        elif stat_upper == "INTUITION":
            # ANTICIPATE: Swap positions
            winner.x, winner.y, loser.x, loser.y = loser.x, loser.y, winner.x, winner.y
            return f"ANTICIPATE! {winner.name} and {loser.name} swap positions!"
            
        elif stat_upper == "CHARM":
            # PSYCHE: Choose where target moves (push in any direction)
            loser.x = max(0, min(self.cols - 1, loser.x + random.choice([-1, 0, 1])))
            loser.y = max(0, min(self.rows - 1, loser.y + random.choice([-1, 0, 1])))
            return f"PSYCHE! {winner.name} redirects {loser.name}'s momentum!"
        
        else:
            # Default: Just stagger (already applied)
            return f"{winner.name} wins the clash!"
    
    # ==================== MAGIC ENGINE ====================
    
    def make_saving_throw(self, caster, target, cast_stat, save_stat, is_sustained=False):
        """
        Contested magic save. 
        Cast: d20 + Cast Stat (sets Target Number)
        Save: d20 + Defense Stat
        Tie on instant = defender wins. Tie on sustained = Magic Clash.
        Returns (success, log, new_target) - new_target may differ if Magic Clash redirects.
        """
        log = []
        
        # Cast Roll
        cast_roll = random.randint(1, 20)
        cast_bonus = caster.get_stat(cast_stat)
        cast_total = cast_roll + cast_bonus
        
        # Save Roll
        save_roll = random.randint(1, 20)
        save_bonus = target.get_stat(save_stat)
        save_total = save_roll + save_bonus
        
        log.append(f"[CAST] {caster.name}: {cast_roll}+{cast_bonus}={cast_total}")
        log.append(f"[SAVE] {target.name}: {save_roll}+{save_bonus}={save_total}")
        
        if cast_total > save_total:
            # Spell hits
            log.append(f"SAVE FAILED! {target.name} is hit by the spell!")
            return (True, log, target)
            
        elif cast_total < save_total:
            # Target saves
            log.append(f"SAVE SUCCESS! {target.name} resists the spell!")
            return (False, log, target)
            
        else:
            # TIE
            if is_sustained:
                # MAGIC CLASH!
                log.append(f"MAGIC CLASH! Rolls tied at {cast_total}!")
                clash_result, clash_log, new_target = self.resolve_magic_clash(
                    caster, target, cast_stat
                )
                log.extend(clash_log)
                return (clash_result, log, new_target)
            else:
                # Instant spell - defender wins ties
                log.append(f"TIE! Defender wins - spell fizzles!")
                return (False, log, target)
    
    def resolve_magic_clash(self, caster, target, cast_stat):
        """
        Magic Clash (Beam Struggle) triggered on ties for sustained spells.
        Cost: Both pay 1 FP/SP extra.
        Re-roll d20 + Stat. Winner's spell resolves, loser is Staggered.
        The stat used determines WHO gets hit (target redirection).
        """
        log = []
        log.append("=== MAGIC CLASH ===")
        
        # Extra cost for clash
        if caster.fp >= 1:
            caster.fp -= 1
            log.append(f"{caster.name} pays 1 FP for the clash!")
        elif caster.sp >= 1:
            caster.sp -= 1
            log.append(f"{caster.name} pays 1 SP for the clash!")
            
        if target.fp >= 1:
            target.fp -= 1
            log.append(f"{target.name} pays 1 FP to resist!")
        elif target.sp >= 1:
            target.sp -= 1
            log.append(f"{target.name} pays 1 SP to resist!")
        
        # Clash Rolls
        caster_roll = random.randint(1, 20) + caster.get_stat(cast_stat)
        target_roll = random.randint(1, 20) + target.get_stat(cast_stat)
        
        log.append(f"{caster.name} channels: {caster_roll}")
        log.append(f"{target.name} resists: {target_roll}")
        
        if caster_roll > target_roll:
            winner, loser = caster, target
            spell_succeeds = True
        elif target_roll > caster_roll:
            winner, loser = target, caster
            spell_succeeds = False
        else:
            # Double tie - both staggered, spell fizzles
            caster.is_staggered = True
            target.is_staggered = True
            log.append("DOUBLE TIE! Magic explodes! Both are STAGGERED!")
            return (False, log, target)
        
        # Loser is staggered
        loser.is_staggered = True
        log.append(f"{loser.name} is STAGGERED!")
        
        # Determine new target based on stat used
        new_target, technique = self.execute_magic_technique(
            winner, loser, caster, target, cast_stat
        )
        log.append(technique)
        
        # Log for replay
        self.replay_log.append({
            "type": "magic_clash",
            "actor": winner.name,
            "target": loser.name,
            "stat": cast_stat,
            "description": technique,
            "result": "caster_wins" if spell_succeeds else "target_wins"
        })
        
        return (spell_succeeds, log, new_target)
    
    def execute_magic_technique(self, winner, loser, caster, original_target, stat):
        """
        Execute magic targeting based on stat used in clash.
        Returns (new_target, description).
        """
        stat_upper = stat.upper() if stat else "WILLPOWER"
        
        if stat_upper == "WILLPOWER":
            # DOMINATE: Spell hits intended target (no deviation)
            return (original_target, f"DOMINATE! Spell hits intended target!")
            
        elif stat_upper == "ENDURANCE":
            # OVERCOME: Reflected back to losing caster
            return (loser, f"OVERCOME! Spell reflects back to {loser.name}!")
            
        elif stat_upper == "KNOWLEDGE":
            # CALCULATE: New target near original target
            nearby = [c for c in self.combatants if c.is_alive() and c != original_target 
                     and max(abs(c.x - original_target.x), abs(c.y - original_target.y)) <= 2]
            if nearby:
                new_t = random.choice(nearby)
                return (new_t, f"CALCULATE! Spell redirects to {new_t.name}!")
            return (original_target, f"CALCULATE! No nearby targets - hits original!")
            
        elif stat_upper == "AWARENESS":
            # SPOT: New target near losing caster
            nearby = [c for c in self.combatants if c.is_alive() and c != loser 
                     and max(abs(c.x - loser.x), abs(c.y - loser.y)) <= 2]
            if nearby:
                new_t = random.choice(nearby)
                return (new_t, f"SPOT! Spell targets {new_t.name} near {loser.name}!")
            return (loser, f"SPOT! No nearby targets - hits {loser.name}!")
            
        elif stat_upper == "REFLEXES":
            # DEFLECT: Random target within 30ft (6 tiles)
            nearby = [c for c in self.combatants if c.is_alive() 
                     and max(abs(c.x - caster.x), abs(c.y - caster.y)) <= 6]
            if nearby:
                new_t = random.choice(nearby)
                return (new_t, f"DEFLECT! Spell wildly redirects to {new_t.name}!")
            return (original_target, f"DEFLECT! No targets in range!")
            
        elif stat_upper == "VITALITY":
            # CENTER: Closest to winner (point blank)
            candidates = [c for c in self.combatants if c.is_alive() and c != winner]
            if candidates:
                closest = min(candidates, 
                             key=lambda c: max(abs(c.x - winner.x), abs(c.y - winner.y)))
                return (closest, f"CENTER! Point blank blast hits {closest.name}!")
            return (original_target, f"CENTER! No targets nearby!")
        
        else:
            return (original_target, f"{winner.name} wins the magic clash!")

    def get_combatant_at(self, x, y):
        """Returns the living combatant at x,y or None."""
        for c in self.combatants:
            if int(c.x) == int(x) and int(c.y) == int(y) and c.hp > 0:
                return c
        return None

    def add_combatant(self, combatant, x, y):
        combatant.x = x
        combatant.y = y
        self.combatants.append(combatant)

    def start_combat(self):
        for c in self.combatants: 
             c.roll_initiative()
             c.movement_remaining = c.movement # Reset at start
             c.action_used = False
             c.bonus_action_used = False
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)
        self.turn_order = self.combatants
        self.current_turn_idx = 0
        return [f"Combat Started! {self.turn_order[0].name}'s Turn."]

    def get_active_char(self):
        if not self.turn_order: return None
        return self.turn_order[self.current_turn_idx]

    def start_turn(self, combatant):
        """
        Called when a combatant's turn begins.
        Returns False if turn is skipped (Stunned/Paralyzed), True otherwise.
        """
        log = []
        
        # Reset attacks received for multi-attacker system
        combatant.attacks_received_this_round = 0
        
        # 0. TERRAIN DAMAGE - Check tile combatant is standing on
        if 0 <= combatant.x < self.cols and 0 <= combatant.y < self.rows:
            tile = self.tiles[combatant.y][combatant.x]
            terrain = tile.terrain.lower() if tile.terrain else "floor_stone"
            
            if terrain == "fire":
                dmg = random.randint(1, 6)
                combatant.take_damage(dmg)
                log.append(f"{combatant.name} takes {dmg} Fire damage from standing in flames!")
                self.replay_log.append({
                    "type": "terrain_damage",
                    "actor": combatant.name,
                    "damage": dmg,
                    "terrain": "fire",
                    "description": f"Burned by fire tile!"
                })
            elif terrain == "ice":
                if random.random() < 0.3:  # 30% slip chance
                    log.append(f"{combatant.name} slips on the ice and loses half their movement!")
                    combatant.movement_remaining = max(0, combatant.movement_remaining // 2)
            elif terrain in ["water", "water_shallow"]:
                log.append(f"{combatant.name} trudges through water (slowed).")
                combatant.movement_remaining = max(0, combatant.movement_remaining - 5)
            elif terrain in ["mud", "difficult", "rubble"]:
                log.append(f"{combatant.name} struggles through difficult terrain.")
                combatant.movement_remaining = max(0, combatant.movement_remaining - 5)
        
        # 1. Tick Start-of-Turn Effects (KILL tier DoTs)
        if hasattr(combatant, 'is_burning') and combatant.is_burning:
            dmg = random.randint(1, 6)  # BURN = 1d6
            combatant.take_damage(dmg)
            log.append(f"{combatant.name} takes {dmg} BURN damage!")
            
        if hasattr(combatant, 'is_bleeding') and combatant.is_bleeding:
            dmg = random.randint(1, 4)  # BLEED = 1d4
            combatant.take_damage(dmg)
            log.append(f"{combatant.name} takes {dmg} BLEED damage!")

        # 2. Check Conditions
        if hasattr(combatant, 'is_frozen') and combatant.is_frozen:
             log.append(f"{combatant.name} is FROZEN solid and skips their turn!")
             return False, log

        if combatant.is_stunned:
             log.append(f"{combatant.name} is STUNNED and skips their turn!")
             return False, log
             
        if combatant.is_paralyzed:
             log.append(f"{combatant.name} is PARALYZED and skips their turn!")
             return False, log
             
        if combatant.is_confused:
            # 50% chance to act normally
            if random.random() < 0.5:
                 log.append(f"{combatant.name} is CONFUSED but maintains focus!")
            else:
                 log.append(f"{combatant.name} moves wildly in CONFUSION!")
                 # Logic for random action would go here. For now, skip turn (flail).
                 return False, log
             
        return True, log

    def end_turn(self):
        # Tick effects on current character before ending
        active = self.turn_order[self.current_turn_idx]
        
        # Tick End-of-Turn Effects (Buffs)
        expired = active.tick_effects() # Renamed/Modified logic below? 
        # For now, keep tick_effects as general ticker
        
        log = []
        if expired:
            log.append(f"Effects expired on {active.name}: {', '.join(expired)}")
        
        self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
    
        # Check Round Cycle
        if self.current_turn_idx == 0:
            self.round_counter += 1
            self.tick_hazards()
            if self.log_callback: self.log_callback(f"--- Round {self.round_counter} ---")

        # Skip dead
        start = self.current_turn_idx
        while not self.turn_order[self.current_turn_idx].is_alive():
            self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
            if self.current_turn_idx == start: break # Everyone dead
        
        # Reset movement for new active char
        new_active = self.turn_order[self.current_turn_idx]
        new_active.movement_remaining = new_active.movement
        # Reset Actions
        new_active.action_used = False
        new_active.bonus_action_used = False
        new_active.reaction_used = False
        
        # TRIGGER START TURN logic for new active
        can_act, start_log = self.start_turn(new_active)
        log.extend(start_log)
        
        if not can_act:
             # Recursively end turn if skipped? 
             # Or just return log and let caller see they can't act.
             # Better: automatically skip to next.
             # CAUTION: Recursive loop if everyone stunning.
             # For safety, just set their actions to used or invalid?
             # Simple approach: If not can_act, we assume the UI/AI loop handles it.
             # But since 'end_turn' is called by UI button...
             # If I skip here, who updates UI?
             # Let's just return the log saying they are stunned. 
             # The UI should disable buttons if 'is_stunned'.
             # Or better, we auto-end their turn? 
             pass

        log.append(f"{new_active.name}'s Turn. (Speed: {new_active.movement_remaining})")
        return log

    def execute_ai_turn(self, ai_char):
        """
        Execute a turn for an AI-controlled character.
        Returns action log.
        """
        # USE NEW AI ENGINE IF AVAILABLE
        if self.ai:
            return self.ai.evaluate_turn(ai_char, self)
            
        # --- FALLBACK LEGACY LOGIC ---
        log = [f"[AI] {ai_char.name} thinks (Legacy)..."]
        
        # Get AI template from data
        ai_template = ai_char.data.get("AI", "Aggressive")
        
        # STATUS OVERRIDE: Berserk -> Force Aggressive + Attack Nearest (Friend or Foe)
        if ai_char.is_berserk:
             ai_template = "Berserk" # Handled below
             
        # Find targets (other living combatants)
        # Normal AI: Enemies only
        # Berserk/Confused: Might target allies
        targets = []
        if ai_template == "Berserk":
             targets = [c for c in self.combatants if c.is_alive() and c != ai_char] # Everyone is a target
        else:
             targets = [c for c in self.combatants if c.is_alive() and c != ai_char] # Simplified Team check later? 
             # Currently no Teams. Everyone is enemy of everyone in deathmatch.
             pass
        if not targets:
            log.append(f"[AI] No targets found.")
            return log
        
        target = targets[0] # Simple: pick first target
        
        # Calculate distance
        dx = abs(ai_char.x - target.x)
        dy = abs(ai_char.y - target.y)
        dist_sq = max(dx, dy)
        
        if ai_template == "Aggressive":
            # Charge and attack
            if dist_sq > 1:
                # Move toward target
                move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Move: {msg}")
                # Try again until in range or out of movement
                while ai_char.movement_remaining >= 5 and max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) > 1:
                    move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                    move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                    ok, msg = self.move_char(ai_char, move_x, move_y)
                    if not ok: break
            
            # Attack if adjacent
            if max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) <= 1:
                attack_log = self.attack_target(ai_char, target)
                log.extend(attack_log)
            else:
                log.append(f"[AI] Couldn't reach {target.name}.")
                
        elif ai_template == "Defensive":
            # Only attack if already adjacent
            if dist_sq <= 1:
                attack_log = self.attack_target(ai_char, target)
                log.extend(attack_log)
            else:
                log.append(f"[AI] Waiting (Defensive)")
                
        elif ai_template == "Ranged":
            # Strategy: Maintain Distance (Range 3-5) and Attack/Cast
            ideal_range = 4
            
            # 1. MOVEMENT (Kiting)
            # If too close (<= 2), run away
            if dist_sq <= 2:
                # Move AWAY from target
                move_x = ai_char.x - (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y - (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Kiting: {msg}")
            
            # If too far (> 5), move closer
            elif dist_sq > 5:
                move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Closing: {msg}")
                
            # 2. ACTION (Cast or Attack)
            # Recalculate distance after move
            dx = abs(ai_char.x - target.x)
            dy = abs(ai_char.y - target.y)
            new_dist = max(dx, dy)
            
            # Try Casting Spell first (if available)
            casted = False
            # Try Casting Spell first (if available)
            casted = False
            # Fix: Check SP or FP (since we don't know which stat uses which yet, assume 2 is min cost)
            if ai_char.powers and (ai_char.sp >= 2 or ai_char.fp >= 2):
                 import random
                 # Priority: Control if target free, then Damage
                 control_spells = [p for p in ai_char.powers if "Entangle" in p or "Sleep" in p or "Stun" in p or "Push" in p]
                 damage_spells = [p for p in ai_char.powers if p not in control_spells]
                 
                 chosen_spell = None
                 # Check status (assuming properties exist, or check active_effects list)
                 is_controlled = target.is_restrained or target.is_stunned or target.is_grappled
                 
                 # Mix up strategy: 70% focus on control, 30% just blast 'em
                 wants_control = (not is_controlled and control_spells and random.random() < 0.7)
                 
                 if wants_control:
                     chosen_spell = random.choice(control_spells)
                     log.append(f"[AI] Prioritizing Control: {chosen_spell}")
                 elif damage_spells:
                     chosen_spell = random.choice(damage_spells)
                     msg = "Prioritizing Damage" if is_controlled else "Mixing it up (Damage)"
                     log.append(f"[AI] {msg}: {chosen_spell}")
                 
                 if chosen_spell:
                     res = self.activate_ability(ai_char, chosen_spell, target)
                     log.extend(res)
                     casted = True
                 
            if not casted:
                # Fallback to Attack if in range
                rng = ai_char.get_attack_range()
                if new_dist <= rng:
                    log.extend(self.attack_target(ai_char, target))
                else:
                    log.append(f"[AI] Target out of range ({new_dist} > {rng}).")
            
        elif ai_template == "Berserker":
            # Random movement + attack
            import random
            move_x = ai_char.x + random.choice([-1, 0, 1])
            move_y = ai_char.y + random.choice([-1, 0, 1])
            self.move_char(ai_char, move_x, move_y)
            if max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) <= 1:
                log.extend(self.attack_target(ai_char, target))
            else:
                log.append(f"[AI] Berserker flails wildly!")
        else:
            log.append(f"[AI] Unknown template: {ai_template}")
            
        return log

    def move_char(self, char, tx, ty):
        # Boundaries
        if not (0 <= tx < self.cols and 0 <= ty < self.rows):
            return False, "Out of Bounds!"

        # Calculate distance
        dist = max(abs(char.x - tx), abs(char.y - ty)) * 5 # 5ft per square
        
        # Check Status: Restrained/Grappled -> Speed 0
        if char.is_restrained or char.is_grappled:
            return False, "You are Restrained/Grappled and cannot move!"
            
        # Check Status: Prone -> Half Speed (Cost double?)
        # For now, simplistic: If Prone, movement costs double?
        # Or require "Stand Up" action?
        # Simplest: Prone = -2 Movement or similar?
        # Let's say Prone costs 2x movement.
        if char.is_prone:
            dist *= 2
            
        if dist > char.movement_remaining:
            return False, f"Not enough movement! ({char.movement_remaining} left)"
        
        # Check collision
        for c in self.combatants:
            if c.is_alive() and c != char and c.x == tx and c.y == ty:
                # BURT'S UPDATE: Collision Check with Talent Exception
                can_pass = getattr(char, "can_move_through_enemies", False)
                if not can_pass:
                    return False, "Blocked!"
                else:
                    # Logic for "Sharing Space" mechanics?
                    # For now we allow them to enter the square.
                    pass
        
        if (tx, ty) in self.walls:
            # Talent Check: Phase Walking / Ghost
            if not getattr(char, "can_phase_walk", False):
                return False, "Blocked by Wall!"
                
        old_x, old_y = char.x, char.y
        char.x = tx
        char.y = ty
        char.movement_remaining -= dist
        
        # --- RECORD EVENT (PROTOCOL 1) ---
        self.replay_log.append({
            "type": "move",
            "actor": char.name,
            "pos_from": [old_x, old_y],
            "pos_to": [tx, ty],
            "timestamp": time.time()
        })
        # ---------------------------------
        
        return True, f"Moved to {tx},{ty}. ({char.movement_remaining} left)"

    # [DELETED DUPLICATE]


    # [CLEANUP] Removed duplicate legacy method body.


    def cast_power(self, caster, target, power_data, save_type="Willpower"):
        """
        Cast a power/spell with opposed roll saving throw.
        caster: The one casting
        target: The one being affected
        power_data: dict with 'Name', 'Stat', 'Effect', etc.
        save_type: How the target chooses to resist (Endurance/Reflex/Fortitude/Willpower/Intuition)
        """
        power_name = power_data.get("Name", "Unknown Power")
        power_stat = power_data.get("Stat", "Knowledge") # Default casting stat
        effect_desc = power_data.get("Effect", "")
        
        log = [f"{caster.name} casts {power_name} on {target.name}!"]
        
        # Capture HP for diff
        start_hp = target.hp

        # Caster rolls d20 + Power Stat (Mod)
        caster_roll = random.randint(1, 20)
        caster_mod = caster.get_stat_modifier(power_stat)
        caster_total = caster_roll + caster_mod
        log.append(f"Caster Roll: {caster_total} ({caster_roll}+{caster_mod} {power_stat})")
        
        # Target rolls d20 + Chosen Save Stat
        target_total, target_nat = target.roll_save(save_type)
        target_mod = target_total - target_nat
        log.append(f"Save Roll ({save_type}): {target_total} ({target_nat}+{target_mod})")
        
        # Context for effects
        ctx = {
            "attacker": caster,
            "target": target,
            "engine": self,
            "log": [],
            "caster_total": caster_total,
            "save_total": target_total,
            "save_success": target_total >= caster_total,
            "is_crit": caster_roll == 20
        }
        
        if target_total >= caster_total:
            log.append(f"{target.name} resists! (Save Success)")
            # Some effects still apply on save (half damage, etc.)
            ctx["save_success"] = True
        else:
            log.append(f"{target.name} fails to resist!")
            ctx["save_success"] = False
            # Apply full effect
            from abilities.effects_registry import registry
            registry.resolve(effect_desc, ctx)
        
        if ctx["log"]:
            log.extend(ctx["log"])
            
        # Calc actual damage dealt
        damage_dealt = start_hp - target.hp
        if caster_roll == 20:
            style += " crit"

        # --- BURT'S PROTOCOL: RECORD CAST EVENT ---
        self.replay_log.append({
            "type": "cast",
            "actor": caster.name,
            "target": target.name,
            "ability": power_name,
            "result": "resist" if ctx["save_success"] else "hit",
            "damage": damage_dealt,
            "target_hp": target.hp,
            "style": style,
            "roll": caster_total,
            "save": target_total
        })
        
        # Check Death (Manual check since cast_power calculated diff manually)
        if target.hp == 0 and start_hp > 0:
             log.append(f"{target.name} is SLAIN by {power_name}!")
             self.replay_log.append({
                "type": "death",
                "actor": target.name,
                "x": target.x,
                "y": target.y
             })
        # ------------------------------------------
        # ------------------------------------------

        return log

    def activate_ability(self, char, ability_name, target=None, **kwargs):
        destination_name = target.name if target else "Self/Area"
        log = [f"{char.name} uses {ability_name} on {destination_name}!"]
        
        # Capture HP for diff (if target exists)
        start_hp = target.hp if target else 0

        # Context
        ctx = {
            "attacker": char,
            "engine": self,
            "log": [],
            "target": target,
            "tier": 1  # Default tier, updated below
        }
        
        try:
            # Lookup Data
            data_item = engine_hooks.get_ability_data(ability_name)
            
            # Get tier for damage scaling
            if data_item and data_item.get("Tier"):
                try:
                    ctx["tier"] = int(data_item.get("Tier"))
                except:
                    pass
            
            if data_item:
                # 1. Determine Cost and Resource Type
                physical_stats = ['Might', 'Reflexes', 'Finesse', 'Endurance', 'Vitality', 'Fortitude']
                attr = data_item.get('Attribute', '')
                
                # Physical stats use SP, Mental stats use FP
                res = 'SP' if attr in physical_stats else 'FP'
                
                # Cost = Tier for School abilities, else 2
                tier = data_item.get('Tier')
                if tier:
                    try:
                        val = int(tier)
                    except:
                        val = 2
                else:
                    val = 2
                
                # Check affordability
                curr = char.sp if res == 'SP' else char.fp
                if curr < val:
                    log.append(f'Not enough {res}! Need {val}, have {curr}.')
                    return log
                    
                # Consume resource
                if res == 'SP': 
                    char.sp -= val
                else: 
                    char.fp -= val
                log.append(f'Consumed {val} {res}')

                # 2. Resolve Effect
                effect_str = data_item.get("Effect") or data_item.get("Description")
                if effect_str:
                    from abilities.effects_registry import registry
                    handled = registry.resolve(effect_str, ctx)
                    if not handled: log.append("No effect resolved (or unimplemented).")
                else:
                    log.append("No Effect Description.")
            else:
                log.append(f"Ability data not found for '{ability_name}'.")

            # --- RECORD EVENT ---
            pos_from = [char.x, char.y]
            pos_to = None
            if target:
                pos_to = [target.x, target.y]
            elif "target_pos" in kwargs:
                pos_to = kwargs["target_pos"]
                
            self.replay_log.append({
                "type": "ability",
                "actor": char.name,
                "ability": ability_name,
                "pos_from": pos_from,
                "pos_to": pos_to,
                "timestamp": time.time()
            })
            # --------------------

        except Exception as e:
            log.append(f"FAILED: {e}")
            
        log.extend(ctx["log"])
        
        # Calc actual damage
        damage_dealt = 0
        if target:
            damage_dealt = start_hp - target.hp
        
        style = self._get_ability_style(ability_name)

        # --- BURT'S PROTOCOL: RECORD ABILITY EVENT ---
        self.replay_log.append({
            "type": "ability",
            "actor": char.name,
            "ability": ability_name,
            "target": target.name if target else "Self",
            "description": f"Used {ability_name}",
            "execution_log": log, # DEBUG INFO
            "damage": damage_dealt,
            "target_hp": target.hp if target else 0,
            "style": style
        })
        
        # Check Death
        if target and target.hp == 0 and start_hp > 0:
             log.append(f"{target.name} is DESTROYED by {ability_name}!")
             self.replay_log.append({
                "type": "death",
                "actor": target.name,
                "x": target.x,
                "y": target.y
             })
        # ---------------------------------------------
        # ---------------------------------------------
        
        return log

    def calc_damage(self, attacker, margin):
        dice = "1d4"; w_name = "Unarmed"
        for item in attacker.inventory:
            if item in self.weapon_db:
                dice = self.weapon_db[item]; w_name = item
                break
        
        try:
            num, sides = map(int, dice.split('d'))
            roll = sum(random.randint(1, sides) for _ in range(num))
        except: roll = 1
            
        bonus = attacker.get_stat("Might")
        return max(1, roll + bonus), w_name

    def resolve_clash(self, choice):
        p1, p2 = self.clash_participants
        if not p1 or not p2: return ["Clash Error"]
        stat = self.clash_stat 
        
        # USE MODIFIERS
        r1 = random.randint(1, 20) + p1.get_stat_modifier(stat)
        r2 = random.randint(1, 20) + p2.get_stat_modifier(stat)
        
        log = [f"CLASH ROLL ({choice}): {p1.name}({r1}) vs {p2.name}({r2})"]
        
        winner = p1 if r1 >= r2 else p2
        loser = p2 if winner == p1 else p1
        
        effect_desc = "Impact"
        s_key = stat.lower()
        
        # Spatial helpers
        dx = loser.x - winner.x
        dy = loser.y - winner.y
        # Normalize to 1 (direction)
        dir_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dir_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        if "might" in s_key or "endurance" in s_key:
            # Push Back 1
            loser.x += dir_x
            loser.y += dir_y
            effect_desc = "Pushed Back"
            if "might" in s_key: # Winner Follows
                winner.x += dir_x
                winner.y += dir_y
                effect_desc += " & Follow Up"
                
        elif "finesse" in s_key:
            effect_desc = "Disarmed (Status Applied)"
            
        elif "reflex" in s_key:
            # Swap
            temp_x, temp_y = winner.x, winner.y
            winner.x, winner.y = loser.x, loser.y
            loser.x, loser.y = temp_x, temp_y
            effect_desc = "Positions Swapped"
            
        elif "knowledge" in s_key or "intuition" in s_key:
            # Move Beside (Flank essentially)
            # Try to move winner to valid adjacent spot? 
            # Simplified: Winner moves to x+dir_y, y+dir_x (Rotated 90)
            winner.x += dir_y
            winner.y += dir_x
            effect_desc = "Flanking Position"
            
        elif "logic" in s_key or "vitality" in s_key:
             dmg = 2
             if "logic" in s_key: loser.hp -= dmg; effect_desc = "2 HP Dmg"
             else: loser.cmp -= dmg; effect_desc = "2 CMP Dmg"
             
        elif "fortitude" in s_key:
            # Loser sideways, Winner forward
             loser.x += dir_y
             loser.y += dir_x
             winner.x += dir_x
             winner.y += dir_y
             effect_desc = "Bulwark Shove"
             
        elif "charm" in s_key:
             # Winner Side Step, Loser Stumble Forward 2
             winner.x += dir_y
             winner.y += dir_x
             loser.x += (dir_x * 2)
             loser.y += (dir_y * 2)
             effect_desc = "Matador Feint"
        
        elif "willpower" in s_key:
             # Move Behind
             winner.x = loser.x + dir_x
             winner.y = loser.y + dir_y
             effect_desc = "Domination (Behind)"
             
        else:
             effect_desc = "Shoved"

        log.append(f"{winner.name} WINS! {effect_desc}")
        
        self.clash_active = False
        self.clash_participants = (None, None)
        return log
