import json
import os
import random

class EnemyGenerator:
    """
    Procedural Enemy Generator based on the Philosophy:
    Rank + Role + Loadout + Species = Monster
    """
    def __init__(self, data_path):
        self.data_path = data_path
        with open(data_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f).get("enemy_builder_v1", {})

    def generate_enemy(self, species_name="Cultist", icon="sheet:5076", base_hp=25, base_sp=10):
        """Generates a fully statted enemy entity for the VTT."""
        
        ranks = list(self.config.get("1_RANK", {}).get("options", {}).keys())
        roles = list(self.config.get("2_ROLE", {}).get("options", {}).keys())
        offenses = list(self.config.get("3_OFFENSE", {}).get("options", {}).keys())
        defenses = list(self.config.get("4_DEFENSE", {}).get("options", {}).keys())
        tactics = list(self.config.get("5_TACTIC", {}).get("options", {}).keys())

        # Fallbacks just in case JSON is malformed
        if not ranks: return self._fallback(species_name, icon, base_hp, base_sp)

        rank_key = random.choice(ranks)
        role_key = random.choice(roles)
        offense_key = random.choice(offenses)
        defense_key = random.choice(defenses)
        tactic_key = random.choice(tactics)

        rank_data = self.config["1_RANK"]["options"][rank_key]
        role_data = self.config["2_ROLE"]["options"][role_key]
        offense_data = self.config["3_OFFENSE"]["options"][offense_key]
        defense_data = self.config["4_DEFENSE"]["options"][defense_key]
        tactic_data = self.config["5_TACTIC"]["options"][tactic_key]

        hp_mult = rank_data.get("hp_mult", 1.0)
        final_hp = int(base_hp * hp_mult)
        
        dmg_mult = rank_data.get("damage_mult", 1.0)
        
        full_name = f"{rank_key.title()} {species_name} {role_key.title()}"
        
        # Build Stats Dict
        stats = {
            "Rank": rank_key,
            "Role": role_key,
            "Size": rank_data.get("size", "Medium"),
            "Behavior": role_data.get("ai_behavior", "Basic"),
            "Weapon": offense_data.get("tag", "Fists"),
            "Damage": offense_data.get("dmg", "Bludgeoning"),
            "Effect": offense_data.get("effect", "None"),
            "Armor": defense_data.get("desc", "Unarmored"),
            "Tactic": tactic_data.get("action", "None")
        }

        # Build VTT Entity
        return {
            "id": f"enemy_{random.randint(1000, 99999)}",
            "name": full_name,
            "type": "enemy",
            "pos": [0, 0], # To be overridden by spawner
            "icon": icon,
            "hp": final_hp,
            "maxHp": final_hp,
            "sp": base_sp,
            "maxSp": base_sp,
            "stats": stats,
            "tags": ["enemy", "hostile", rank_key.lower()],
            "inventory": []
        }

    def _fallback(self, name, icon, hp, sp):
        return {
            "id": f"enemy_{random.randint(1000, 99999)}",
            "name": name,
            "type": "enemy",
            "pos": [0, 0],
            "icon": icon,
            "hp": hp,
            "maxHp": hp,
            "sp": sp,
            "maxSp": sp,
            "stats": {"Behavior": "Basic"},
            "tags": ["enemy", "hostile"],
            "inventory": []
        }

if __name__ == "__main__":
    gen = EnemyGenerator(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Enemy_Builder.json"))
    print(json.dumps(gen.generate_enemy(), indent=4))
