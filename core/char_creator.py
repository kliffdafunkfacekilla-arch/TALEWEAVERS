import json
import os

class CharacterBuilder:
    """
    Logic for deriving T.T.S. (Tactical Triad System) attributes from base stats.
    """
    
    SPECIES_TRAITS = {
        "HUMAN": {"bonus_stats": {"Willpower": 1, "Determination": 1}, "traits": ["Versatile"]},
        "AQUATIC": {"bonus_stats": {"Endurance": 2}, "traits": ["Amphibious", "Ink Jet"]},
        "AVIAN": {"bonus_stats": {"Reflexes": 2}, "traits": ["Flight", "Keen Sight"]},
        "STONY": {"bonus_stats": {"Fortitude": 2}, "traits": ["Damage Reduction", "Slow"]},
    }

    @staticmethod
    def calculate_derived_stats(stats):
        """
        Derives resource pools from core attributes.
        Formulas:
        - HP (Health): Vitality + Fortitude + (Endurance / 2)
        - SP (Stamina): Endurance + Might + (Reflexes / 2)
        - FP (Focus): Knowledge + Logic + (Willpower / 2)
        - CMP (Composure): Willpower + Intuition + (Awareness / 2)
        """
        vit = stats.get("Vitality", 10)
        fort = stats.get("Fortitude", 10)
        end = stats.get("Endurance", 10)
        mig = stats.get("Might", 10)
        ref = stats.get("Reflexes", 10)
        knw = stats.get("Knowledge", 10)
        log = stats.get("Logic", 10)
        wil = stats.get("Willpower", 10)
        intui = stats.get("Intuition", 10)
        awa = stats.get("Awareness", 10)

        hp = int(vit + fort + (end / 2))
        sp = int(end + mig + (ref / 2))
        fp = int(knw + log + (wil / 2))
        cmp = int(wil + intui + (awa / 2))

        return {
            "HP": hp,
            "maxHp": hp,
            "SP": sp,
            "maxSp": sp,
            "FP": fp,
            "maxFp": fp,
            "CMP": cmp,
            "maxCmp": cmp
        }

    @classmethod
    def create_new_character(cls, name, species, stats):
        """
        Processes stats and species to create a full character dictionary.
        """
        species_data = cls.SPECIES_TRAITS.get(species.upper(), {"bonus_stats": {}, "traits": []})
        
        # Apply species bonuses
        final_stats = stats.copy()
        for stat, bonus in species_data.get("bonus_stats", {}).items():
            if stat in final_stats:
                final_stats[stat] += bonus
            else:
                final_stats[stat] = bonus

        derived = cls.calculate_derived_stats(final_stats)
        
        character = {
            "Name": name,
            "Species": species.upper(),
            "Level": 1,
            "Stats": final_stats,
            "Traits": species_data.get("traits", []),
            "Inventory": [],
            "Equipped": {
                "HEAD": None,
                "BODY": None,
                "ARMS": None,
                "LEGS": None,
                "MAIN_HAND": None,
                "OFF_HAND": None
            },
            "Gold": 10
        }
        character.update(derived)
        return character

if __name__ == "__main__":
    # Test
    test_stats = {
        "Might": 10, "Endurance": 10, "Reflexes": 10,
        "Vitality": 10, "Fortitude": 10, "Knowledge": 10,
        "Logic": 10, "Willpower": 10, "Intuition": 10, "Awareness": 10
    }
    char = CharacterBuilder.create_new_character("TestHero", "HUMAN", test_stats)
    print(json.dumps(char, indent=4))
