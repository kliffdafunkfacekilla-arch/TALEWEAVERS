import uuid
from typing import Dict, List, Any, Optional

class Entity:
    """
    The fundamental object in the ECS. 
    It is merely a container for a unique ID and a collection of Components.
    """
    def __init__(self, name="Unnamed Entity"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.components: Dict[str, Any] = {}

    def add_component(self, component):
        self.components[type(component).__name__] = component
        return self

    def get_component(self, component_type):
        """
        Retrieves a component by its class type.
        Example: entity.get_component(Position)
        """
        return self.components.get(component_type.__name__)

    def has_component(self, component_type):
        return component_type.__name__ in self.components

    def __repr__(self):
        return f"<Entity {self.name} ({self.id})>"

# --- COMPONENTS ---

class Position:
    """Logical position in the world (Grid or Graph node)."""
    def __init__(self, x=0, y=0, z=0, map_id=None):
        self.x = x
        self.y = y
        self.z = z
        self.map_id = map_id  # For multi-map support

class Renderable:
    """Visual representation for the VTT."""
    def __init__(self, icon="token.png", color="#ffffff", scale=1.0, layer=1):
        self.icon = icon
        self.color = color
        self.scale = scale
        self.layer = layer

class Stats:
    """Core attributes (Might, Finesse, etc)."""
    def __init__(self, stats_dict: Dict[str, int] = None):
        self.attrs = stats_dict or {}

    def get(self, stat_name, default=0):
        return self.attrs.get(stat_name, default)

    def set(self, stat_name, value):
        self.attrs[stat_name] = value

class Vitals:
    """Dynamic survival resources (HP, SP, FP)."""
    def __init__(self, hp=10, max_hp=10, sp=10, max_sp=10, fp=10, max_fp=10):
        self.hp = hp
        self.max_hp = max_hp
        self.sp = sp
        self.max_sp = max_sp
        self.fp = fp
        self.max_fp = max_fp

class Inventory:
    """Carried items."""
    def __init__(self, capacity=20):
        self.items = [] # List of Item objects or dicts
        self.capacity = capacity
        self.gold = 0

class Equipment:
    """Currently worn/wielded items."""
    def __init__(self):
        self.slots = {
            "Main Hand": None,
            "Off Hand": None,
            "Armor": None,
            "Head": None,
            "Accessory": None
        }

class AIController:
    """Flags this entity as controlled by the AI Engine."""
    def __init__(self, behavior_tree="default", aggression=0.5):
        self.behavior_tree = behavior_tree
        self.aggression = aggression
        self.target_id = None

class PlayerController:
    """Flags this entity as controlled by a human user."""
    def __init__(self, user_id="p1"):
        self.user_id = user_id

class StatusEffects:
    """Active buffs/debuffs."""
    def __init__(self):
        self.active_effects = []  # List of {name, duration, magnitude}

class FactionMember:
    """Allegiance data."""
    def __init__(self, faction_name="Neutral", rank=0):
        self.faction_name = faction_name
        self.rank = rank

# --- SYSTEMS (Micro-Managers) ---
"""
Systems in ECS typically iterate over entities with specific components.
In Python, we can define them as functions or classes that take a list of entities.
"""

class ECSRegistry:
    """target for all entities"""
    def __init__(self):
        self.entities: Dict[str, Entity] = {}

    def add_entity(self, entity: Entity):
        self.entities[entity.id] = entity

    def get_entities_with(self, *component_types):
        """
        Returns a generator of entities that have ALL specified components.
        Example: registry.get_entities_with(Position, Renderable)
        """
        for entity in self.entities.values():
            if all(entity.has_component(c) for c in component_types):
                yield entity
