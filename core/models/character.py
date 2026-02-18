from typing import Dict, Any, List, Optional
from .item import Item
from core.ecs import Entity, Position, Vitals, Stats, Renderable, Inventory, Equipment, StatusEffects, FactionMember

class Character(Entity):
    """
    Represents a Player Character or NPC.
    Holds Stats, Skills, Powers, and Inventory using ECS Components.
    """
    def __init__(self, data: Any):
        if isinstance(data, str):
            data = {"Name": data}
        
        super().__init__(data.get("Name", data.get("name", "Unnamed")))
        
        # Add ECS Components
        self.add_component(Position())
        self.add_component(Renderable())
        self.add_component(Stats())
        self.add_component(Vitals())
        self.add_component(Inventory())
        self.add_component(Equipment())
        self.add_component(StatusEffects())
        self.add_component(FactionMember())
        
        # Keep original data for passthrough of specialized fields (Traits, Backstory, etc.)
        self.raw_data = data.copy()
        
        # Data Normalization & Component Hydration
        self.species = data.get("Species", data.get("species", "Unknown"))
        self.get_component(Stats).attrs = data.get("Stats", data.get("stats", {}))
        self.skills = data.get("Skills", data.get("skills", []))
        self.powers = data.get("Powers", data.get("powers", []))
        self.traits = data.get("Traits", data.get("traits", []))
        self.backstory = data.get("Backstory", data.get("backstory", ""))
        
        # Sprite/Portrait Sync
        sprite = data.get("Sprite", data.get("sprite", data.get("Portrait", data.get("portrait", "badger_front.png"))))
        if sprite and not sprite.endswith('.png'):
            sprite += ".png"
            
        r = self.get_component(Renderable)
        r.icon = sprite
        r.color = data.get("Color", data.get("color", "#ffffff"))

        self.ai_archetype = data.get("AI_Archetype", data.get("ai_archetype", "Berserker"))
        self.level = data.get("Level", data.get("level", 1))
        
        # Resource Pools (Initialize Vitals)
        self._sync_vitals_from_stats(data)
        
        # Inventory & Equipment Hydration
        raw_inv = data.get("Inventory", data.get("inventory", []))
        inv_comp = self.get_component(Inventory)
        
        from core.stubs import DataLoader
        dl = DataLoader()
        
        for item_entry in raw_inv:
            if isinstance(item_entry, str):
                item_data = dl.get_item_data(item_entry)
                inv_comp.items.append(Item(item_data if item_data else {"Name": item_entry}))
            elif isinstance(item_entry, dict):
                inv_comp.items.append(Item(item_entry))

        # Equipment Mapping
        self.equipment_slots = data.get("Equipment", data.get("equipment", {}))
        gear = data.get("Gear", data.get("gear", {}))
        
        if gear:
            if "rightHand" in gear and gear["rightHand"]: 
                self.equipment_slots["Main Hand"] = gear["rightHand"].get("Name") if isinstance(gear["rightHand"], dict) else gear["rightHand"]
            if "leftHand" in gear and gear["leftHand"]:
                self.equipment_slots["Off Hand"] = gear["leftHand"].get("Name") if isinstance(gear["leftHand"], dict) else gear["leftHand"]
            if "armor" in gear and gear["armor"]:
                self.equipment_slots["Armor"] = gear["armor"].get("Name") if isinstance(gear["armor"], dict) else gear["armor"]

        equipped_names = set()
        for val in self.equipment_slots.values():
            if val and val != "Empty":
                 equipped_names.add(val)
                 
        for item in inv_comp.items:
            if item.name in equipped_names:
                item.is_equipped = True

    def _sync_vitals_from_stats(self, data=None):
        v = self.get_component(Vitals)
        s = self.get_component(Stats)
        
        v.max_hp = 10 + s.get("Might", 10) + s.get("Vitality", 10) + s.get("Reflexes", 10)
        v.max_sp = s.get("Endurance", 10) + s.get("Finesse", 10) + s.get("Fortitude", 10)
        v.max_fp = s.get("Knowledge", 10) + s.get("Charm", 10) + s.get("Intuition", 10)
        
        # CMP (Composure) - If we want to keep it as a custom pool, we might need a custom component 
        # For now, let's use a dynamic attribute or just stick to the 3 standard ones.
        self.max_cmp = 10 + s.get("Willpower", 10) + s.get("Logic", 10) + s.get("Awareness", 10)
        
        if data:
            v.hp = data.get("Current_HP", data.get("current_hp", v.max_hp))
            v.sp = data.get("Current_SP", data.get("sp", data.get("current_sp", v.max_sp)))
            v.fp = data.get("Current_FP", data.get("fp", data.get("current_fp", v.max_fp)))
            self.current_cmp = data.get("Current_CMP", data.get("cmp", data.get("current_cmp", self.max_cmp)))
        else:
            v.hp = v.max_hp
            v.sp = v.max_sp
            v.fp = v.max_fp
            self.current_cmp = self.max_cmp

    # --- LEGACY PROPERTY ADAPTERS (Hard Migration: Redirecting to ECS) ---

    @property
    def stats(self): return self.get_component(Stats).attrs
    @stats.setter
    def stats(self, val): self.get_component(Stats).attrs = val

    @property
    def hp(self): return self.get_component(Vitals).hp
    @hp.setter
    def hp(self, val): self.get_component(Vitals).hp = val

    @property
    def current_hp(self): return self.get_component(Vitals).hp
    @current_hp.setter
    def current_hp(self, val): self.get_component(Vitals).hp = val

    @property
    def max_hp(self): return self.get_component(Vitals).max_hp
    @max_hp.setter
    def max_hp(self, val): self.get_component(Vitals).max_hp = val

    @property
    def sp(self): return self.get_component(Vitals).sp
    @sp.setter
    def sp(self, val): self.get_component(Vitals).sp = val

    @property
    def fp(self): return self.get_component(Vitals).fp
    @fp.setter
    def fp(self, val): self.get_component(Vitals).fp = val

    @property
    def inventory(self): return self.get_component(Inventory).items

    @property
    def sprite(self): return self.get_component(Renderable).icon
    @sprite.setter
    def sprite(self, val): self.get_component(Renderable).icon = val

    @property
    def x(self): return self.get_component(Position).x
    @x.setter
    def x(self, val): self.get_component(Position).x = val

    @property
    def y(self): return self.get_component(Position).y
    @y.setter
    def y(self, val): self.get_component(Position).y = val

    def get_stat_mod(self, name: str) -> int:
        val = self.get_component(Stats).get(name, 10)
        return (val - 10) // 2

    def get_equipped_weapon(self) -> Dict[str, Any]:
        for item in self.inventory:
            if item.is_equipped and item.type == "Weapon":
                return item.data
        return {"Name": "Unarmed Strike", "Damage": "1d4", "Stat": "Might"}

    def to_dict(self) -> Dict[str, Any]:
        """Export for storage or frontend, maintaining original data passthrough."""
        v = self.get_component(Vitals)
        out = self.raw_data.copy()
        out.update({
            "name": self.name,
            "species": self.species,
            "stats": self.stats,
            "inventory": [i.name for i in self.inventory],
            "equipment": self.equipment_slots,
            "sprite": self.sprite,
            "powers": [p.get("Name") if isinstance(p, dict) else p for p in self.powers],
            "skills": self.skills,
            "traits": self.traits,
            "current_hp": v.hp,
            "max_hp": v.max_hp,
            "sp": v.sp,
            "max_sp": v.max_sp,
            "fp": v.fp,
            "max_fp": v.max_fp,
            "cmp": self.current_cmp,
            "max_cmp": self.max_cmp,
            "level": self.level,
            "x": self.x,
            "y": self.y
        })
        return out
