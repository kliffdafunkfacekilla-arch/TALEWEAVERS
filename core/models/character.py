from typing import Dict, Any, List, Optional
from .item import Item

class Character:
    """
    Represents a Player Character or NPC.
    Holds Stats, Skills, Powers, and Inventory.
    """
    def __init__(self, data: Any):
        if isinstance(data, str):
            data = {"Name": data}
        
        # Keep original data for passthrough of specialized fields (Traits, Backstory, etc.)
        self.raw_data = data.copy()
        
        # Data Normalization
        self.name = data.get("Name", data.get("name", "Unnamed"))
        self.species = data.get("Species", data.get("species", "Unknown"))
        self.stats = data.get("Stats", data.get("stats", {}))
        self.skills = data.get("Skills", data.get("skills", []))
        self.powers = data.get("Powers", data.get("powers", []))
        self.traits = data.get("Traits", data.get("traits", []))
        self.backstory = data.get("Backstory", data.get("backstory", ""))
        
        # Sprite/Portrait Sync
        self.sprite = data.get("Sprite", data.get("sprite", data.get("Portrait", data.get("portrait", "badger_front.png"))))
        if self.sprite and not self.sprite.endswith('.png'):
            self.sprite += ".png"
            
        self.ai_archetype = data.get("AI_Archetype", data.get("ai_archetype", "Berserker"))
        self.level = data.get("Level", data.get("level", 1))
        
        # Resource Pools
        self.max_hp = self._calculate_max_hp()
        self.current_hp = data.get("Current_HP", data.get("current_hp", self.max_hp))
        
        self.max_sp = self._calculate_max_sp()
        self.sp = data.get("Current_SP", data.get("sp", data.get("current_sp", self.max_sp)))
        
        self.max_fp = self._calculate_max_fp()
        self.fp = data.get("Current_FP", data.get("fp", data.get("current_fp", self.max_fp)))
        
        self.max_cmp = self._calculate_max_cmp()
        self.cmp = data.get("Current_CMP", data.get("cmp", data.get("current_cmp", self.max_cmp)))
        
        # Inventory & Equipment Hydration
        self.inventory: List[Item] = []
        raw_inv = data.get("Inventory", data.get("inventory", []))
        
        from core.stubs import DataLoader
        dl = DataLoader()
        
        for item_entry in raw_inv:
            if isinstance(item_entry, str):
                item_data = dl.get_item_data(item_entry)
                self.inventory.append(Item(item_data if item_data else {"Name": item_entry}))
            elif isinstance(item_entry, dict):
                self.inventory.append(Item(item_entry))

        # Equipment Mapping
        self.equipment = data.get("Equipment", data.get("equipment", {}))
        gear = data.get("Gear", data.get("gear", {}))
        
        if gear:
            if "rightHand" in gear and gear["rightHand"]: 
                self.equipment["Main Hand"] = gear["rightHand"].get("Name") if isinstance(gear["rightHand"], dict) else gear["rightHand"]
            if "leftHand" in gear and gear["leftHand"]:
                self.equipment["Off Hand"] = gear["leftHand"].get("Name") if isinstance(gear["leftHand"], dict) else gear["leftHand"]
            if "armor" in gear and gear["armor"]:
                self.equipment["Armor"] = gear["armor"].get("Name") if isinstance(gear["armor"], dict) else gear["armor"]

        equipped_names = set()
        for val in self.equipment.values():
            if val and val != "Empty":
                 equipped_names.add(val)
                 
        for item in self.inventory:
            if item.name in equipped_names:
                item.is_equipped = True

    def _calculate_max_hp(self) -> int:
        might = self.stats.get("Might", 10)
        vit = self.stats.get("Vitality", 10)
        reflex = self.stats.get("Reflexes", 10)
        return 10 + might + vit + reflex

    def _calculate_max_sp(self) -> int:
        endurance = self.stats.get("Endurance", 10)
        finesse = self.stats.get("Finesse", 10)
        fortitude = self.stats.get("Fortitude", 10)
        return endurance + finesse + fortitude

    def _calculate_max_fp(self) -> int:
        knowledge = self.stats.get("Knowledge", 10)
        charm = self.stats.get("Charm", 10)
        intuition = self.stats.get("Intuition", 10)
        return knowledge + charm + intuition

    def _calculate_max_cmp(self) -> int:
        willpower = self.stats.get("Willpower", 10)
        logic = self.stats.get("Logic", 10)
        awareness = self.stats.get("Awareness", 10)
        return 10 + willpower + logic + awareness

    def get_stat_mod(self, name: str) -> int:
        val = self.stats.get(name, 10)
        return (val - 10) // 2

    def get_equipped_weapon(self) -> Dict[str, Any]:
        for item in self.inventory:
            if item.is_equipped and item.type == "Weapon":
                return item.data
        return {"Name": "Unarmed Strike", "Damage": "1d4", "Stat": "Might"}

    def to_dict(self) -> Dict[str, Any]:
        """Export for storage or frontend, maintaining original data passthrough."""
        out = self.raw_data.copy()
        out.update({
            "name": self.name,
            "species": self.species,
            "stats": self.stats,
            "inventory": [i.name for i in self.inventory],
            "equipment": self.equipment,
            "sprite": self.sprite,
            "powers": [p.get("Name") if isinstance(p, dict) else p for p in self.powers],
            "skills": self.skills,
            "traits": self.traits,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "sp": self.sp,
            "max_sp": self.max_sp,
            "fp": self.fp,
            "max_fp": self.max_fp,
            "cmp": self.cmp,
            "max_cmp": self.max_cmp,
            "level": self.level
        })
        return out
