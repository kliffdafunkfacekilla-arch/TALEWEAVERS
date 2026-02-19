import random
from core.ecs import world_ecs

class EnemySpawner:
    """
    Prefab Factory for spawning ECS-native enemies.
    """
    @staticmethod
    def spawn_at(name, x, y, sprite="sheet:5076", faction="Hostile"):
        data = {
            "Name": name,
            "x": x,
            "y": y,
            "Sprite": sprite,
            "Team": faction,
            "Stats": {
                "Might": 12, "Vitality": 10, "Fortitude": 8, "Endurance": 10,
                "Reflexes": 10, "Knowledge": 5, "Logic": 5, "Willpower": 8
            }
        }
        # This registers the entity in the global ECS AND saves to SQLite
        entity = world_ecs.create_character(data)
        entity.add_tag("hostile")
        print(f"[SPAWNER] Spawned {name} at ({x}, {y})")
        return entity

# Singleton accessor
spawner = EnemySpawner()
