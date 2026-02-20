from core.ecs import world_ecs, Position, Vitals, Renderable
from typing import Dict, Any, Tuple, List
import random

class InteractionEngine:
    """
    Deterministically processes 'INTERACT' and 'USE' intents.
    Applies strict logic to ECS tags (breakable, lockable, container, explosive).
    Returns mechanical logs and state updates, stripping mathematics away from the Narrative LLM.
    """
    
    @staticmethod
    def resolve_interaction(intent: Dict[str, Any], player_data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        target_name = intent.get('target', 'nothing')
        if not target_name or target_name == 'nothing':
            return "You interact with the air nothing happens.", []
            
        # 1. Find the target in the ECS radius
        player_pos = player_data.get('pos', [500, 500])
        target_entity = None
        
        for e in world_ecs.entities.values():
            if target_name.lower() in e.id.lower() or target_name.lower() in e.name.lower():
                target_entity = e
                break
                
        if not target_entity:
            return f"System: Could not find '{target_name}' nearby.", []
            
        tags = set(target_entity.tags)
        action_verb = intent.get('action', 'INTERACT')
        flavor = intent.get('narrative_flavor', '')
        
        updates = []
        result_log = []
        
        # 2. Process based on ECS Tags
        if 'breakable' in tags and any(word in flavor.lower() for word in ['bash', 'smash', 'hit', 'break', 'kick']):
            result_log.append(f"System: The {target_entity.name} is shattered.")
            updates.append({"type": "DESTROY_ENTITY", "id": target_entity.id})
            
            if 'container' in tags:
                loot = InteractionEngine.generate_loot(target_entity)
                result_log.append(f"System: Revealed contents: {loot}")
                updates.append({"type": "SPAWN_LOOT", "pos": [player_pos[0], player_pos[1]], "items": loot})
            
            if 'explosive' in tags:
                dmg = random.randint(5, 15)
                result_log.append(f"System: BOOM! {target_entity.name} explodes dealing {dmg} damage in an AoE.")
                updates.append({"type": "DAMAGE_AOE", "damage": dmg, "radius": 2})

            # Remove from ECS
            world_ecs.destroy_entity(target_entity.id)
            
        elif 'switch' in tags or 'lever' in tags:
            activated = False
            if 'active' in tags:
                target_entity.tags.remove('active')
                target_entity.tags.append('inactive')
                result_log.append(f"System: You deactivated the {target_entity.name}.")
            else:
                if 'inactive' in tags: target_entity.tags.remove('inactive')
                target_entity.tags.append('active')
                result_log.append(f"System: You activated the {target_entity.name}.")
                activated = True
                
            # Scan for a linked door / logic gate
            link_tag = next((t for t in tags if str(t).startswith("link_")), None)
            
            for e in world_ecs.entities.values():
                # Either global "door" toggle or specific link match
                if 'door' in e.tags or 'gate' in e.tags:
                    if link_tag is None or link_tag in e.tags:
                        if activated:
                            if 'locked' in e.tags: e.tags.remove('locked')
                            if 'openable' not in e.tags: e.tags.append('openable')
                            result_log.append(f"System: The {e.name} unlocks and opens!")
                            updates.append({"type": "PLAY_ANIMATION", "name": "UNLOCK", "target": e.id})
                        else:
                            if 'openable' in e.tags: e.tags.remove('openable')
                            if 'locked' not in e.tags: e.tags.append('locked')
                            result_log.append(f"System: The {e.name} slams shut and locks.")
            world_ecs.save_entity(target_entity.id, target_entity.name, target_entity.to_dict())
            
        elif 'openable' in tags or 'container' in tags:
            if 'locked' in tags:
                if 'key' in player_data: # Placeholder for inventory check
                    result_log.append(f"System: Used Key. Unlocked {target_entity.name}.")
                    target_entity.tags.remove('locked')
                    world_ecs.save_entity(target_entity.id, target_entity.name, target_entity.to_dict())
                else:
                    result_log.append(f"System: The {target_entity.name} is locked.")
            else:
                loot = InteractionEngine.generate_loot(target_entity)
                result_log.append(f"System: Opened {target_entity.name}. Contents: {loot}")
                updates.append({"type": "SPAWN_LOOT", "pos": [player_pos[0], player_pos[1]], "items": loot})
                target_entity.tags.remove('openable') # already open
                
        elif 'readable' in tags:
            result_log.append(f"System: You read the {target_entity.name}. It contains ancient knowledge.")
            
        elif 'npc' in tags or 'talkable' in tags:
            return "System: Target is an NPC. Use TALK action.", []
            
        else:
            result_log.append(f"System: Attempted interaction with {target_entity.name}, but it lacks affordances.")
            
        final_log = "\n".join(result_log)
        return final_log, updates

    @staticmethod
    def generate_loot(entity) -> List[str]:
        # Simple generic loot drop for Phase 11
        drops = []
        val = random.random()
        if val > 0.8: drops.append("Gold Coin")
        elif val > 0.4: drops.append("Minor Health Potion")
        else: drops.append("Scrap Materials")
        return drops
