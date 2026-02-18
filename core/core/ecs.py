import uuid

class Entity:
    def __init__(self, name="Unnamed Entity"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.components = {}

    def add_component(self, component):
        self.components[type(component).__name__] = component
        return self

    def get_component(self, component_type_name):
        return self.components.get(component_type_name)

    def has_component(self, component_type_name):
        return component_type_name in self.components

# --- Components ---

class Position:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Stats:
    def __init__(self, stats_dict=None):
        self.attrs = stats_dict or {}

class Health:
    def __init__(self, current=10, max_hp=10):
        self.current = current
        self.max = max_hp

class InventoryComponent:
    def __init__(self, capacity=20):
        self.items = []
        self.capacity = capacity

class Actor:
    """Component for entities that can take turns and have AI/Player control."""
    def __init__(self, controller="AI"):
        self.controller = controller # 'AI' or 'Player'

class Renderable:
    def __init__(self, icon="token.png", layer=1):
        self.icon = icon
        self.layer = layer
