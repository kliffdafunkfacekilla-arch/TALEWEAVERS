import json
import os
import random
import math
import sys
import time
from core.ecs import Entity, world_ecs, Position, Vitals, Stats, Renderable

class CombatEngine:
    """
    High-Performance Mechanical Rules Engine (The Math).
    Processes Actions (Intents) and returns mechanical results.
    """
    def __init__(self, cols=20, rows=20):
        self.cols = cols
        self.rows = rows
        self.combatants: List[Entity] = []
        self.walls = set()
        self.active = True
        self.round_count = 1
        self.turn_index = 0
        self.replay_log = []

    def process_intent(self, intent_dict):
        """Routes structured Pydantic intent to mechanics."""
        action = intent_dict.get("action", "TALK").upper()
        target_name = intent_dict.get("target", "")
        params = intent_dict.get("parameters", {})
        
        # Get Player (Assume Burt for now)
        player = next((c for c in self.combatants if "player" in c.name.lower()), None)
        if not player: return "No active player found.", []

        updates = []
        log = []

        if action == "ATTACK":
            target = next((c for c in self.combatants if target_name.lower() in c.name.lower() and c != player), None)
            if target:
                log = self.attack_target(player, target)
                updates.append({"type": "PLAY_ANIMATION", "name": "MELEE", "target": target.name})
                updates.append({"type": "UPDATE_HP", "id": target.name, "hp": target.hp})
            else:
                log = [f"Target {target_name} not found."]

        elif action == "MOVE":
            dx, dy = params.get("dx", 0), params.get("dy", 0)
            ok, msg = self.move_char(player, int(player.x + dx), int(player.y + dy))
            log = [msg]
            if ok: updates.append({"type": "MOVE_TOKEN", "id": player.name, "pos": [player.x, player.y]})

        return " ".join(log), updates

    def attack_target(self, attacker, target, skill_used=None):
        """Margin-Based Resolution."""
        logs = []
        
        # Safe Stat Getters
        atk_stats = attacker.get_component(Stats)
        def_stats = target.get_component(Stats)
        
        atk_might = atk_stats.get("Might", 10) if atk_stats else 10
        def_reflex = def_stats.get("Reflexes", 10) if def_stats else 10
        
        # Skill/Role Modifiers
        skill_bonus = 0
        if skill_used == "STRIKER": skill_bonus = 2
        elif atk_stats and "Role" in atk_stats.attrs:
            # Enemy rank/role math
            role = atk_stats.get("Role", "")
            if role == "BERZERKER": skill_bonus = 3
            elif role == "SNIPER": skill_bonus = 4
            
        atk_roll = random.randint(1, 20) + (atk_might // 2) + skill_bonus
        def_roll = random.randint(1, 20) + (def_reflex // 2)
        
        margin = atk_roll - def_roll
        logs.append(f"{attacker.name} vs {target.name}: {atk_roll} vs {def_roll} (Margin: {margin})")
        
        if margin >= 10: 
            dmg = 15
            if skill_used == "BREAKER": dmg += 10 # Massive shatter
            target.take_damage(dmg)
            logs.append(f"SMASH! {dmg} DMG dealt.")
        elif margin > 0: 
            dmg = 8
            target.take_damage(dmg)
            logs.append(f"Solid Hit! {dmg} DMG dealt.")
        elif margin == 0: 
            logs.append("CLASH! Weapons lock!")
        else:
            logs.append("Miss or Deflected!")
            
        return logs

    def move_char(self, char, tx, ty):
        if not (0 <= tx < self.cols and 0 <= ty < self.rows):
            return False, "Out of Bounds!"
        if (tx, ty) in self.walls:
            return False, "Blocked by Wall!"
            
        char.x, char.y = tx, ty
        return True, f"Moved to {tx},{ty}."
