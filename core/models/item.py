from typing import Dict, Any, List

class Item:
    """
    Represents a Game Item (Weapon, Armor, or Consumable).
    Strictly maps to the schema found in Gear.json.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data  # Store raw data for compatibility
        self.name = data.get("Name", "Unknown")
        self.type = data.get("Type", "Misc")
        self.cost = int(data.get("Cost", 0))
        self.related_skill = data.get("Related_Skill", data.get("Skill", ""))  # Support both keys
        self.skill = data.get("Skill", data.get("Related_Skill", ""))  # Weapon skill for mastery
        self.description = data.get("Description", "")
        self.effect_text = data.get("Effect", "")
        self.logic_tags = self._parse_tags(data.get("Logic_Tags", ""))
        self.is_equipped = data.get("is_equipped", False)
        
        # Helper properties derived from tags
        self.is_weapon = self.type == "Weapon"
        self.is_armor = self.type == "Armor"
        self.is_consumable = self.type == "Consumable" # Logic tag based if needed

    def _parse_tags(self, tag_str: str) -> Dict[str, Any]:
        """
        Parses 'DMG:2d6:Slash|PROP:Heavy' into a dict.
        """
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

    def get_tag(self, key: str, default=None):
        """Safe accessor for logic tags."""
        return self.logic_tags.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dict representation."""
        return {
            "Name": self.name,
            "Type": self.type,
            "Cost": self.cost,
            "Related_Skill": self.related_skill,
            "Description": self.description,
            "Effect": self.effect_text,
            "Logic_Tags": self.logic_tags # Note: we return parsed tags for internal use
        }
