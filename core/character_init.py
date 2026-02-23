import os
import json
from typing import Dict, Any
from core.ecs import Entity, Position, Renderable, Vitals, Stats, Inventory, StatusEffects, FactionMember, world_ecs

class LegacyAdapter:
    """
    Wraps an ECS Entity to provide a legacy-compatible interface.
    Allows older combat logic to read/write 'hp' while mapping to the Vitals component.
    """
    def __init__(self, entity: Entity):
        self._entity = entity

    @property
    def hp(self):
        v = self._entity.get_component(Vitals)
        return v.hp if v else 0

    @hp.setter
    def hp(self, value):
        v = self._entity.get_component(Vitals)
        if v:
            v.hp = value

    @property
    def max_hp(self):
        v = self._entity.get_component(Vitals)
        return v.max_hp if v else 0

    def __getattr__(self, name):
        # Proxy other attributes to the entity or its components
        if hasattr(self._entity, name):
            return getattr(self._entity, name)
        
        # Check components
        for comp in self._entity.components.values():
            if hasattr(comp, name):
                return getattr(comp, name)
        
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

def initialize_character_from_save(save_name: str, x: int = 5, y: int = 5) -> Entity:
    """
    Loads a character from a JSON save file and injects it into the world ECS.
    """
    from brain.dependencies import DATA_DIR
    save_path = os.path.join(DATA_DIR, "Saves", f"{save_name}.json")
    
    if not os.path.exists(save_path):
        raise FileNotFoundError(f"Save file not found: {save_path}")

    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Use existing ECS factory
    entity = world_ecs.create_character(data)
    
    # Override position
    pos = entity.get_component(Position)
    if pos:
        pos.x, pos.y = x, y
    
    # Ensure it's tagged as a player
    entity.add_tag("player")
    
    print(f"[INIT] Character {save_name} injected into ECS at ({x}, {y})")
    return entity

if __name__ == "__main__":
    # Test initialization
    try:
        hero = initialize_character_from_save("Burt")
        legacy_hero = LegacyAdapter(hero)
        print(f"Legacy HP Check: {legacy_hero.hp}/{legacy_hero.max_hp}")
        legacy_hero.hp -= 5
        print(f"Post-Damage HP Check (Legacy): {legacy_hero.hp}")
        print(f"Post-Damage HP Check (ECS): {hero.get_component(Vitals).hp}")
    except Exception as e:
        print(f"Init Test Failed: {e}")
