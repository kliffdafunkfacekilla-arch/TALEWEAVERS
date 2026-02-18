from typing import Dict, Any, List
from core.ecs import Entity, Stats

class Item:
    """
    Factory for Item Entities.
    """
    @staticmethod
    def create(data: Dict[str, Any]) -> Entity:
        name = data.get("Name", "Unknown")
        entity = Entity(name)
        
        # Add Item Components
        entity.add_component(Stats(data.get("Stats", {})))
        
        # Metadata logic from the old class
        entity.metadata.update({
            "type": data.get("Type", "Misc"),
            "cost": int(data.get("Cost", 0)),
            "description": data.get("Description", ""),
            "effect_text": data.get("Effect", ""),
            "logic_tags": Item._parse_tags(data.get("Logic_Tags", "")),
            "skill": data.get("Skill", data.get("Related_Skill", ""))
        })
        
        return entity

    @staticmethod
    def _parse_tags(tag_str: str) -> Dict[str, Any]:
        """Parses 'DMG:2d6:Slash|PROP:Heavy' into a dict."""
        tags = {}
        if not tag_str: return tags
        
        parts = tag_str.split('|')
        for part in parts:
            tokens = part.split(':')
            key = tokens[0]
            # If value is present, store it. If boolean tag, store True.
            # Example: DMG:2d6:Slash -> {'DMG': ['2d6', 'Slash']}
            # Example: PROP:Heavy -> {'PROP': ['Heavy']} note: multiple props should probably be a list 
            # Current logic stores last PROP if duplicate keys exist in simple dict. 
            # Better logic:
            if key in tags:
                if not isinstance(tags[key], list):
                    tags[key] = [tags[key]]
                tags[key].append(tokens[1:] if len(tokens) > 1 else True)
            else:
                 val = tokens[1:] if len(tokens) > 1 else True
                 # Flatten single item lists for convenience if standard
                 if isinstance(val, list) and len(val) == 1:
                     val = val[0]
                 tags[key] = val
        return tags

    @staticmethod
    def to_dict(entity: Entity) -> Dict[str, Any]:
        """Returns JSON-serializable dict representation from an Item Entity."""
        m = entity.metadata
        return {
            "Name": entity.name,
            "Type": m.get("type"),
            "Cost": m.get("cost"),
            "Skill": m.get("skill"),
            "Description": m.get("description"),
            "Effect": m.get("effect_text"),
            "Logic_Tags": m.get("logic_tags")
        }
