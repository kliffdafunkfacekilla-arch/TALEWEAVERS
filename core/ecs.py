import uuid
import json
from typing import Dict, List, Any, Optional
from .database import PersistenceLayer

class Entity:
    """
    The fundamental object in the ECS. 
    It is merely a container for a unique ID and a collection of Components.
    """
    def __init__(self, name="Unnamed Entity"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.components: Dict[str, Any] = {}
        self.tags = set()
        self.metadata = {} 

    def add_component(self, component):
        self.components[type(component).__name__] = component
        return self

    def get_component(self, component_type):
        return self.components.get(component_type.__name__)

    def has_component(self, component_type):
        return component_type.__name__ in self.components

    def add_tag(self, tag: str):
        self.tags.add(tag)
        return self

    def has_tag(self, tag: str):
        return tag in self.tags

    def to_dict(self):
        comp_data = {}
        for name, comp in self.components.items():
            comp_data[name] = vars(comp)
        return {
            "id": self.id,
            "name": self.name,
            "components": comp_data,
            "tags": list(self.tags),
            "metadata": self.metadata
        }

    # --- CORE BEHAVIORS ---
    def is_alive(self):
        v = self.get_component(Vitals)
        return v.hp > 0 if v else False

    def take_damage(self, amount):
        v = self.get_component(Vitals)
        if not v: return 0
        actual = min(amount, v.hp)
        v.hp -= actual
        # Trigger persistence update if world_ecs is managing it
        return actual

    # --- CORE PROPERTY ADAPTERS ---
    @property
    def x(self): 
        c = self.get_component(Position)
        return c.x if c else 0
    @x.setter
    def x(self, val):
        c = self.get_component(Position)
        if c: c.x = val

    @property
    def y(self): 
        c = self.get_component(Position)
        return c.y if c else 0
    @y.setter
    def y(self, val):
        c = self.get_component(Position)
        if c: c.y = val

    @property
    def hp(self):
        c = self.get_component(Vitals)
        return c.hp if c else 0
    @hp.setter
    def hp(self, val):
        c = self.get_component(Vitals)
        if c: c.hp = val

    @property
    def max_hp(self):
        c = self.get_component(Vitals)
        return c.max_hp if c else 0

    @property
    def sp(self):
        c = self.get_component(Vitals)
        return c.sp if c else 0
    @sp.setter
    def sp(self, val):
        c = self.get_component(Vitals)
        if c: c.sp = val

    @property
    def max_sp(self):
        c = self.get_component(Vitals)
        return c.max_sp if c else 0

    @property
    def fp(self):
        c = self.get_component(Vitals)
        return c.fp if c else 0
    @fp.setter
    def fp(self, val):
        c = self.get_component(Vitals)
        if c: c.fp = val

    @property
    def max_fp(self):
        c = self.get_component(Vitals)
        return c.max_fp if c else 0

    @property
    def cmp(self):
        c = self.get_component(Vitals)
        return c.cmp if c else 0
    @cmp.setter
    def cmp(self, val):
        c = self.get_component(Vitals)
        if c: c.cmp = val

    @property
    def max_cmp(self):
        c = self.get_component(Vitals)
        return c.max_cmp if c else 0

# --- COMPONENTS ---
class Position:
    def __init__(self, x=0, y=0, z=0): self.x = x; self.y = y; self.z = z

class Renderable:
    def __init__(self, icon="sheet:5074", color="#ffffff", scale=1.0):
        self.icon = icon; self.color = color; self.scale = scale

class Stats:
    def __init__(self, attrs=None): self.attrs = attrs or {}
    def get(self, name, default=10): return self.attrs.get(name, default)

class Vitals:
    def __init__(self, hp=10, max_hp=10, sp=10, max_sp=10, fp=10, max_fp=10, cmp=10, max_cmp=10):
        self.hp = hp; self.max_hp = max_hp
        self.sp = sp; self.max_sp = max_sp
        self.fp = fp; self.max_fp = max_fp
        self.cmp = cmp; self.max_cmp = max_cmp

class Inventory:
    def __init__(self, capacity=20): self.items = []; self.gold = 0

class StatusEffects:
    def __init__(self): self.active_effects = []

class FactionMember:
    def __init__(self, faction="Neutral"): self.faction_name = faction

class Logistics:
    def __init__(self, resources=None, population=0):
        self.resources = resources or {"Food": 100, "Gold": 100}
        self.population = population
        self.needs = {"Food": 1.0}
        self.last_tick = 0

# --- REGISTRY & FACTORIES ---
class ECSRegistry:
    def __init__(self, db_path="data/world_state.db"):
        self.entities: Dict[str, Entity] = {}
        self.db = PersistenceLayer(db_path)

    def add_entity(self, entity: Entity):
        self.entities[entity.id] = entity
        self.db.save_entity(entity.id, entity.name, entity.to_dict())
        return entity

    def get_entity(self, eid): return self.entities.get(eid)

    def load_all(self):
        """Loads all entities from the SQLite persistence layer into the active registry."""
        rows = self.db.load_all_entities()
        for eid, name, data_json in rows:
            data = json.loads(data_json)
            e = Entity(name)
            e.id = eid
            e.tags = set(data.get("tags", []))
            e.metadata = data.get("metadata", {})
            
            # Reconstruct Components
            comp_data = data.get("components", {})
            for c_name, c_vars in comp_data.items():
                # Map component name to class
                cls = getattr(sys.modules[__name__], c_name, None)
                if cls:
                    comp = cls()
                    for k, v in c_vars.items():
                        setattr(comp, k, v)
                    e.add_component(comp)
            
            self.entities[eid] = e
        print(f"[ECS] Restored {len(self.entities)} entities from database.")

    def create_character(self, data: Dict) -> Entity:
        """Factory: registers character directly into active world state using TTS formulas."""
        e = Entity(data.get("Name", "Hero"))
        e.add_component(Position(data.get("x", 0), data.get("y", 0)))
        e.add_component(Renderable(data.get("Sprite", data.get("Portrait", "sheet:5074"))))
        e.add_component(Stats(data.get("Stats", {})))
        e.add_component(Vitals())
        e.add_component(Inventory())
        e.add_component(StatusEffects())
        e.add_component(FactionMember(data.get("Team", "Neutral")))
        
        # Calculate TTS Vitals
        s = e.get_component(Stats)
        v = e.get_component(Vitals)
        
        v.max_hp = int(s.get("Vitality") + s.get("Fortitude") + (s.get("Endurance") / 2))
        v.max_sp = int(s.get("Endurance") + s.get("Might") + (s.get("Reflexes") / 2))
        v.max_fp = int(s.get("Knowledge") + s.get("Logic") + (s.get("Willpower") / 2))
        v.max_cmp = int(s.get("Willpower") + s.get("Intuition") + (s.get("Awareness") / 2))
        
        v.hp, v.sp, v.fp, v.cmp = v.max_hp, v.max_sp, v.max_fp, v.max_cmp
        
        return self.add_entity(e)

    def get_entities_with(self, *types):
        for e in self.entities.values():
            if all(e.has_component(t) for t in types): yield e

# Singleton
world_ecs = ECSRegistry()
