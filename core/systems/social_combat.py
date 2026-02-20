import random
from typing import Dict, Any, Tuple
from core.ecs import world_ecs, Stats, Vitals

class SocialCombatEngine:
    """
    Handles mechanical resolution for conversational encounters.
    Maps attributes like 'Deception', 'Insight', 'Logic', and 'Willpower' to Composure (CMP) damage.
    """
    def __init__(self):
        # Maps intents to the offensive stat and defensive stat respectively
        # example: "coerce" uses (Might vs Willpower)
        self.action_mapping = {
            "intimidate": ("Might", "Willpower"),
            "deceive": ("Deception", "Intuition"),
            "persuade": ("Logic", "Willpower"),
            "charm": ("Intuition", "Knowledge"),
            "taunt": ("Deception", "Reflexes")
        }

    def resolve_social_action(self, intent: Dict[str, Any], player_data: Dict[str, Any]) -> Tuple[str, list]:
        """
        Executes a social combat action against an NPC.
        Decreases their Composure (CMP) if successful.
        Returns a narrative string describing the mechanics, and any visual updates.
        """
        target_name = intent.get('target', '').lower()
        if not target_name:
            return "You speak to the air. Nothing happens.", []

        # Find the target entity in the ECS
        target_entity = next((e for e in world_ecs.entities.values() if e.name.lower() == target_name), None)
        if not target_entity:
            return f"{target_name.capitalize()} is not here.", []

        if not target_entity.has_component(Stats) or not target_entity.has_component(Vitals):
            return f"{target_entity.name} cannot be reasoned with.", []

        # Attempt to categorize the flavor into an action class
        flavor = intent.get('narrative_flavor', '').lower()
        action_type = "persuade" # default
        for key in self.action_mapping.keys():
            if key in flavor:
                action_type = key
                break

        off_stat_name, def_stat_name = self.action_mapping[action_type]
        
        # Get stats
        p_stats = player_data.get('attributes', {})
        t_stats = target_entity.get_component(Stats)
        t_vitals = target_entity.get_component(Vitals)

        offense = p_stats.get(off_stat_name, 10)
        defense = t_stats.get(def_stat_name, 10)

        # 2d6 Roll vs Target Number
        roll = random.randint(1, 6) + random.randint(1, 6)
        total = roll + offense
        target_number = 10 + defense

        updates = []
        result = ""

        if total >= target_number:
            # Success! Deal Composure damage (1d4 + (offense - defense))
            cmp_dmg = max(1, random.randint(1, 4) + (offense - defense))
            t_vitals.cmp = max(0, t_vitals.cmp - cmp_dmg)
            
            result = f"Attempted to {action_type} {target_entity.name} (Rolled {total} vs {target_number}). Success! Dealt {cmp_dmg} Composure damage."
            updates.append({
                "type": "SOCIAL_DMG",
                "target_id": target_entity.id,
                "amount": cmp_dmg,
                "stat": "cmp",
                "flavor": "Cracked their composure"
            })

            if t_vitals.cmp == 0:
                result += f" {target_entity.name}'s composure breaks! They fold to your demands."
        else:
            result = f"Attempted to {action_type} {target_entity.name} (Rolled {total} vs {target_number}). Failure! They remain steadfast."

        return result, updates

social_engine = SocialCombatEngine()
