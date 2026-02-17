import json
import os
import random

class ItemGenerator:
    """
    Procedural Loot Generator based on the Tactical Triad System.
    """
    
    def __init__(self, data_path):
        self.data_path = data_path
        self.config = self._load_config()
        
    def _load_config(self):
        with open(self.data_path, 'r') as f:
            return json.load(f)["item_system_v1"]

    def generate_loot(self, category=None, max_tier=2):
        """
        Main entry point for generating a procedural item.
        """
        if not category:
            category = random.choice(["WEAPON", "ARMOR"])
            
        if category == "WEAPON":
            return self._generate_weapon(max_tier)
        elif category == "ARMOR":
            return self._generate_armor(max_tier)
        return {"error": "Invalid category"}

    def _generate_weapon(self, max_tier):
        weapon_data = self.config["categories"]["WEAPON"]
        base_type = random.choice(list(weapon_data["types"].keys()))
        base_stats = weapon_data["types"][base_type]
        
        # Select Material
        tier_key = f"Tier {random.randint(1, max_tier)}"
        material = self.config["materials"][tier_key]
        
        # Optional Prefix/Suffix (30% chance each)
        prefix = None
        if random.random() < 0.3:
            prefix = random.choice(list(self.config["enchantments"]["prefix"].keys()))
            
        suffix = None
        if random.random() < 0.3:
            suffix = random.choice(list(self.config["enchantments"]["suffix"].keys()))
            
        # Construct Name
        mat_name = material["name"].split('/')[0] # Get iron from Iron/Hide
        name_parts = []
        if prefix: name_parts.append(prefix)
        name_parts.append(mat_name)
        name_parts.append(base_type)
        if suffix: name_parts.append(suffix)
        
        full_name = " ".join(name_parts)
        
        # Calculate Stats
        dmg_mod = int(material.get("dmg_mod", "+0"))
        final_dmg = f"{base_stats['dmg']}{dmg_mod:+}" if dmg_mod != 0 else base_stats['dmg']
        
        # Loadout Cost
        raw_cost = base_stats["cost"] # e.g. "1 SP"
        cost_val = int(raw_cost.split()[0])
        cost_type = raw_cost.split()[1]
        
        if prefix:
            prefix_data = self.config["enchantments"]["prefix"][prefix]
            cost_val += prefix_data.get("cost_add", 0)
            
        # Material Discount
        discount = material.get("loadout_discount", "0").split()[0]
        cost_val += int(discount) # e.g. -1
        
        cost_val = max(0, cost_val)
        
        return {
            "id": f"item_{random.getrandbits(32)}",
            "name": full_name,
            "category": "WEAPON",
            "base_type": base_type,
            "material": mat_name,
            "stats": {
                "Damage": final_dmg,
                "Property": base_stats["prop"],
                "Cost": f"{cost_val} {cost_type}"
            },
            "traits": [material.get("prop_add")] if material.get("prop_add") else [],
            "effects": [
                self.config["enchantments"]["prefix"][prefix]["effect"] if prefix else None,
                self.config["enchantments"]["suffix"][suffix]["effect"] if suffix else None
            ],
            "rarity": tier_key
        }

    def _generate_armor(self, max_tier):
        armor_data = self.config["categories"]["ARMOR"]
        base_type = random.choice(list(armor_data["types"].keys()))
        base_stats = armor_data["types"][base_type]
        
        tier_key = f"Tier {random.randint(1, max_tier)}"
        material = self.config["materials"][tier_key]
        
        mat_name = material["name"].split('/')[1] if '/' in material["name"] else material["name"]
        full_name = f"{mat_name} {base_type}"
        
        raw_cost = base_stats["cost"]
        cost_val = int(raw_cost.split()[0])
        cost_type = raw_cost.split()[1]
        
        # Material Discount
        discount = material.get("loadout_discount", "0").split()[0]
        cost_val += int(discount)
        cost_val = max(0, cost_val)

        return {
            "id": f"item_{random.getrandbits(32)}",
            "name": full_name,
            "category": "ARMOR",
            "base_type": base_type,
            "material": mat_name,
            "stats": {
                "Protection": base_stats["prot"],
                "Cost": f"{cost_val} {cost_type}",
                "Trait": base_stats.get("trait")
            },
            "rarity": tier_key
        }

if __name__ == "__main__":
    # Test
    gen = ItemGenerator(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "Item_Builder.json"))
    for _ in range(3):
        item = gen.generate_loot()
        print(json.dumps(item, indent=4))
