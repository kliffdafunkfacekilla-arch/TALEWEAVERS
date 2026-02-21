import json
import os
import random
import math
import heapq
from typing import List, Dict, Any, Optional
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
        self.terrain: Dict[tuple, str] = {} # (x, y) -> "DIFFICULT", "ACID", "LAVA", "POISON", "ACID_BARREL", "LAVA_PIPE", etc.
        self.items: Dict[tuple, str] = {} # (x, y) -> "MIGHT_VIAL", "SPEED_VIAL", etc.
        self.elevation: Dict[tuple, int] = {} # (x, y) -> height level (0, 1, 2)
        self.threat: Dict[str, Dict[str, float]] = {} # npc_id -> {target_id: threat_value}
        self.grid_cells = None # Reference to visual grid [row][col]
        self.active = True
        self.round_count = 1
        self.turn_index = 0
        self.replay_log = []
        self.pending_updates = [] # Visual triggers for the frontend to consume
        self.reactions_used = set() # Track per-round limited reactions

    def has_los(self, x0, y0, x1, y1):
        """Bresenham LOS check."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for i in range(n):
            if (x, y) in self.walls and (x, y) != (x0, y0) and (x, y) != (x1, y1):
                return False
            if x == x1 and y == y1:
                return True
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
        return True

    def find_path(self, start, goal):
        """A* Pathfinding implementation."""
        def heuristic(a, b):
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

        frontend = [(0, start)]
        came_from = {}
        cost_so_far = {start: 0}

        while frontend:
            current = heapq.heappop(frontend)[1]
            if current == goal: break

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    neighbor = (current[0] + dx, current[1] + dy)
                    if not (0 <= neighbor[0] < self.cols and 0 <= neighbor[1] < self.rows): continue
                    if neighbor in self.walls: continue
                        
                    move_cost = 1
                    t_type = self.terrain.get(neighbor)
                    if t_type == "DIFFICULT": move_cost = 2
                    
                    # Add danger weight for AI pathing
                    danger = self.get_tile_danger_score(neighbor[0], neighbor[1])
                    move_cost += danger * 5 # High penalty for hazards
                    
                    new_cost = cost_so_far[current] + move_cost
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + heuristic(goal, neighbor)
                        heapq.heappush(frontend, (priority, neighbor))
                        came_from[neighbor] = current

        if goal not in came_from: return []
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    def apply_damage_with_resistance(self, target: Entity, dmg: int, dmg_type: str):
        """Applies damage accounting for active resistances and triggers Adaptive Carapace."""
        final_dmg = dmg
        logs = []
        updates = []
        
        # Check Resistance
        if hasattr(target, "status_effects"):
            resist_type = f"RESIST_{dmg_type.upper()}"
            if any(s["type"] == resist_type for s in target.status_effects):
                final_dmg = max(1, dmg // 2)
                logs.append(f"[RESISTED] {target.name}'s shell softens the {dmg_type} impact! (-50% DMG)")
                updates.append({"type": "FCT", "text": "RESISTED", "pos": [target.x, target.y], "style": "dmg"})
        
        # --- Goo Puddle Heat Vulnerability ---
        t_terrain = self.terrain.get((target.x, target.y))
        if dmg_type == "HEAT" and t_terrain == "GOO":
            final_dmg *= 2
            logs.append(f"[VULNERABLE] {target.name} is coated in Goo! Double Heat damage.")

        target.take_damage(final_dmg)
        
        # --- Symbiotic Bond Splitting ---
        if hasattr(target, "symbiotic_link") and target.symbiotic_link:
            partner = next((c for c in self.combatants if c.id == target.symbiotic_link), None)
            if partner and partner.hp > 0:
                share = final_dmg // 2
                if share > 0:
                    target.hp += share # Give back half
                    partner.take_damage(share)
                    logs.append(f"[SYMBIO] {target.name} shares the pain with {partner.name}! (-{share} HP shared)")
                    updates.append({"type": "FCT", "text": f"-{share} LINK", "pos": [partner.x, partner.y], "style": "dmg"})
                    updates.append({"type": "UPDATE_HP", "id": partner.id, "hp": partner.hp})

        # Trigger Adaptive Carapace
        traits = getattr(target, 'metadata', {}).get("Traits", {})
        if "Adaptive Carapace" in traits:
            # Shield grows for NEXT round
            resist_to_add = f"RESIST_{dmg_type.upper()}"
            if not hasattr(target, "status_effects"): target.status_effects = []
            if not any(s["type"] == resist_to_add for s in target.status_effects):
                target.status_effects.append({"type": resist_to_add, "duration": 2}) # 2 rounds (current and next)
                logs.append(f"[ADAPT] {target.name}'s carapace hardens against {dmg_type}!")
                updates.append({"type": "FCT", "text": "ADAPTED", "pos": [target.x, target.y], "style": "react"})

        return final_dmg, logs, updates

    def process_intent(self, intent_dict):
        """Routes structured Pydantic intent to mechanics."""
        action = intent_dict.get("action", "TALK").upper()
        target_id = intent_dict.get("target", "")
        params = intent_dict.get("parameters", {})
        
        player = next((c for c in self.combatants if "hero" in c.tags), None)
        if not player: return "No active hero found.", []

        updates = []
        log = []

        if action == "ATTACK":
            target = next((c for c in self.combatants if c.id == target_id), None)
            if not target:
                target = next((c for c in self.combatants if target_id.lower() in c.name.lower() and c != player), None)
            
            if target:
                if not self.has_los(player.x, player.y, target.x, target.y):
                    log = [f"Cannot see {target.name}! Line of sight blocked."]
                else:
                    atk_logs, atk_updates = self.attack_target(player, target)
                    log.extend(atk_logs)
                    updates.extend(atk_updates)
                    updates.append({"type": "UPDATE_HP", "id": target.id, "hp": target.hp})
                    updates.append({"type": "UPDATE_HP", "id": player.id, "hp": player.hp})
                    updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
            else:
                log = [f"Target {target_id} not found."]

        elif action == "MOVE":
            dx, dy = params.get("dx", 0), params.get("dy", 0)
            ok, msg, move_updates = self.move_char(player, int(player.x + dx), int(player.y + dy))
            log = [msg]
            updates.extend(move_updates)
            if ok: 
                updates.append({"type": "MOVE_TOKEN", "id": player.id, "pos": [player.x, player.y]})
                updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
                updates.append({"type": "UPDATE_HP", "id": player.id, "hp": player.hp})
                
        elif action == "SMASH":
            tx, ty = params.get("x", 0), params.get("y", 0)
            ok, msg, smash_updates = self.smash_tile(player, tx, ty)
            log = [msg]
            updates.extend(smash_updates)
            if ok:
                updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
                # Note: smash_tile sends its own GRID_UPDATEs or terrain removals

        elif action == "SKILL":
            skill_name = params.get("skill_name", "")
            tx, ty = params.get("x", 0), params.get("y", 0)
            log_msg, skill_updates = self.use_skill(player, skill_name, tx, ty)
            log = [log_msg]
            updates.extend(skill_updates)
            updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
            for c in self.combatants:
                updates.append({"type": "UPDATE_HP", "id": c.id, "hp": c.hp})
                updates.append({"type": "MOVE_TOKEN", "id": c.id, "pos": [c.x, c.y]})

        return " ".join(log), updates

    def get_effective_stat(self, char: Entity, stat_name: str):
        """Calculates stat value including base stats and temporary buffs."""
        stats = char.get_component(Stats)
        base = stats.get(stat_name, 10) if stats else 10
        bonus = 0
        if hasattr(char, "temp_buffs"):
            for b in char.temp_buffs:
                if b["stat"].lower() == stat_name.lower():
                    bonus += b["bonus"]
        if hasattr(char, "status_effects"):
            for s in char.status_effects:
                if s["type"] == "ENRAGED":
                    if stat_name.lower() == "might": bonus += 5
                    if stat_name.lower() == "reflexes": bonus -= 5
                if s["type"] == "PHEROMONES":
                    if stat_name.lower() in ["might", "reflexes"]: bonus += 2
        return base + bonus

    def handle_reactions(self, source: Entity, target: Entity, trigger: str, context: Dict[str, Any]):
        """Processes Evolutionary Trait Reactions."""
        logs = []
        v_updates = []
        traits = getattr(target, 'metadata', {}).get("Traits", {})
        
        for name, mechanic in traits.items():
            if "danger sense" in name.lower() and trigger == "BEFORE_ATTACK":
                reaction_key = f"{target.id}_dangersense_{self.round_count}"
                if reaction_key not in self.reactions_used:
                    self.reactions_used.add(reaction_key)
                    bonus = 5
                    context["def_bonus"] = context.get("def_bonus", 0) + bonus
                    logs.append(f"[REACTION] {target.name}'s Danger Sense flares up! (+{bonus} Defense)")
                    v_updates.append({"type": "FCT", "text": "DANGER SENSE", "pos": [target.x, target.y], "style": "react"})

            if ("thorns" in name.lower() or "spines" in name.lower()) and trigger == "POST_DAMAGE":
                recoil = 2
                source.hp -= recoil
                logs.append(f"[REACTION] {source.name} is pricked by {target.name}'s spines! ({recoil} Recoil DMG)")
                v_updates.append({"type": "FCT", "text": f"-{recoil} RECOIL", "pos": [source.x, source.y], "style": "dmg"})

            if "reactive camo" in name.lower() and trigger == "BEFORE_ATTACK":
                if random.random() < 0.25:
                    context["force_miss"] = True
                    logs.append(f"[REACTION] {target.name}'s Camo blurs their form!")
                    v_updates.append({"type": "FCT", "text": "BLURRED", "pos": [target.x, target.y], "style": "react"})

        return logs, v_updates

    def smash_tile(self, char, tx, ty):
        """Might-based environmental destruction."""
        t_type = self.terrain.get((tx, ty))
        is_bush = t_type == "DIFFICULT"
        is_trigger = t_type in ["ACID_BARREL", "LAVA_PIPE"]
        is_bridge = t_type == "WOODEN_BRIDGE"
        
        if (tx, ty) not in self.walls and not is_bush and not is_trigger and not is_bridge:
            return False, "There is nothing robust to smash here.", []
            
        dist = max(abs(char.x - tx), abs(char.y - ty))
        if dist > 1: return False, "Target too far to smash.", []
        sp_cost = 3
        if char.sp < sp_cost: return False, f"Too exhausted to smash! (Need {sp_cost} SP)", []
        
        might = self.get_effective_stat(char, "Might")
        check = random.randint(1, 20) + (might // 2)
        threshold = 12 if (is_bush or is_trigger) else 15
        char.sp -= sp_cost
        
        updates = []
        if check >= threshold:
            if is_bush:
                del self.terrain[(tx, ty)]
                updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                return True, f"{char.name} TRAMPLES the brush into nothing!", [{"type": "FCT", "text": "BUSH DESTROYED", "pos": [tx, ty], "style": "react"}]
            elif is_trigger:
                h_type = "ACID" if t_type == "ACID_BARREL" else "LAVA"
                del self.terrain[(tx, ty)]
                updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                logs = [f"{char.name} SMASHES the {t_type}! {h_type} spills everywhere!"]
                updates.append({"type": "AOE_PULSE", "pos": [tx, ty], "radius": 2, "color": "#84cc16" if h_type == "ACID" else "#ef4444"})
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = tx + dx, ty + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.walls:
                            self.terrain[(nx, ny)] = h_type
                            updates.append({"type": "GRID_UPDATE", "x": nx, "y": ny, "cell": 131 if h_type == "ACID" else 132})
                return True, " ".join(logs), updates
            elif is_bridge:
                # Bridge Collapse
                del self.terrain[(tx, ty)]
                # Reveal underlying hazard based on neighbors (Dynamic)
                neighbors = []
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    n_type = self.terrain.get((tx + dx, ty + dy))
                    if n_type in ["ACID", "LAVA"]: neighbors.append(n_type)
                
                new_h = random.choice(neighbors) if neighbors else None
                if new_h:
                    self.terrain[(tx, ty)] = new_h
                    updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 131 if new_h == "ACID" else 132})
                else:
                    updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                
                updates.append({"type": "SHAKE", "intensity": 8})
                logs = [f"The WOODEN BRIDGE collapses into the {new_h.lower() if new_h else 'ground'}!"]
                
                victim = next((c for c in self.combatants if c.x == tx and c.y == ty and c.hp > 0), None)
                if victim:
                    final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(victim, 10, "IMPACT")
                    logs.extend(d_logs)
                    updates.extend(d_updates)
                    logs.append(f"{victim.name} falls with the debris! (-{final_dmg} HP)")
                    updates.append({"type": "FCT", "text": "COLLAPSE", "pos": [tx, ty], "style": "crit"})
                    
                    # Trigger immediate hazard effect if it fell into one
                    hx_logs, hx_updates = self.check_tile_effects(victim)
                    logs.extend(hx_logs)
                    updates.extend(hx_updates)
                
                return True, " ".join(logs), updates
            else:
                self.walls.remove((tx, ty))
                if self.grid_cells: self.grid_cells[ty][tx] = 129
                updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                return True, f"{char.name} SMASHES the obstacle into rubble!", [{"type": "SHAKE", "intensity": 8}, {"type": "FCT", "text": "SMASH!", "pos": [tx, ty], "style": "crit"}]
        return False, f"{char.name} strikes the obstacle, but it holds firm.", [{"type": "FCT", "text": "CLANG", "pos": [tx, ty], "style": "dmg"}]

    def use_skill(self, char, skill_name, tx, ty):
        """Processes active evolutionary abilities and generic spellcasts."""
        orig_skill_name = skill_name
        skill_name = skill_name.upper()
        logs = []
        updates = []
        
        # Elevation Range Bonus
        h_bonus = 0
        char_h = self.elevation.get((char.x, char.y), 0)
        target_h = self.elevation.get((tx, ty), 0)
        if char_h > target_h:
            h_bonus = char_h - target_h
            logs.append(f"[HIGH GROUND] Range increased by {h_bonus}!")

        # ------------------------------------------------------------------
        # --- GENERIC SPELL RESOLUTION (Phase 47) ---
        # ------------------------------------------------------------------
        # Lazy load Schools_of_Power
        if not getattr(self, "_schools_of_power", None):
            matrix_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Schools_of_Power.json")
            try:
                with open(matrix_path, 'r', encoding='utf-8') as f:
                    self._schools_of_power = json.load(f)
            except Exception as ex:
                self._schools_of_power = {"schools": {}}
                
        # Search for spell across all schools
        spell_data = None
        for school_name, school_info in self._schools_of_power.get("schools", {}).items():
            for sp in school_info.get("spells", []):
                if sp["name"].upper() == skill_name:
                    spell_data = sp
                    break
            if spell_data: break
            
        if spell_data:
            sp_cost = spell_data.get("tier", 1) * 2 # Formula: Tier x 2 = SP Cost
            if char.sp < sp_cost: 
                return f"Not enough SP for {orig_skill_name}! (Requires {sp_cost})", []
            
            dist = max(abs(char.x - tx), abs(char.y - ty))
            max_range = 4 + h_bonus + spell_data.get("tier", 1) # Range scales with tier
            if dist > max_range: 
                return f"Target out of range ({max_range} tiles).", []
                
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            
            logic_tag = spell_data.get("logic_tag", "UNKNOWN")
            dmg_type = spell_data.get("damage_type", "FORCE").upper()
            
            # Color mapping based on element
            color_map = {
                "FIRE": "#ef4444", "HEAT": "#ef4444", "COLD": "#60a5fa",
                "POISON": "#10b981", "ACID": "#84cc16", "SHOCK": "#fde047",
                "FORCE": "#a8a29e", "RADIANT": "#fcd34d", "NECROTIC": "#7e22ce"
            }
            proj_color = color_map.get(dmg_type, "#ffffff")
            updates.append({"type": "PROJECTILE", "from": [char.x, char.y], "to": [tx, ty], "color": proj_color})

            if target:
                if logic_tag.startswith("OFFENSE"):
                    # Generic Offensive Damage
                    dmg = spell_data.get("tier", 1) * 5 # Base damage formula
                    final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, dmg_type)
                    logs.extend(d_logs)
                    updates.extend(d_updates)
                    
                    if "hero" in char.tags and "hero" not in target.tags:
                        self.apply_threat(target, char, final_dmg)
                        
                    logs.append(f"{char.name} casts {orig_skill_name} on {target.name}! ({final_dmg} {dmg_type} DMG)")
                    updates.append({"type": "FCT", "text": f"-{final_dmg} {dmg_type}", "pos": [tx, ty], "style": "dmg"})
                    
                    # Specific tag sub-handlers
                    if "PUSH" in logic_tag:
                        dx = 1 if tx > char.x else (-1 if tx < char.x else 0)
                        dy = 1 if ty > char.y else (-1 if ty < char.y else 0)
                        nx, ny = target.x + dx, target.y + dy
                        if not any(c.x == nx and c.y == ny for c in self.combatants) and (nx, ny) not in self.walls:
                            target.x, target.y = nx, ny
                            updates.append({"type": "MOVE_TOKEN", "id": target.id, "pos": [nx, ny]})
                            logs.append(f"{target.name} is knocked back!")
                            hx_logs, hx_updates = self.check_tile_effects(target)
                            logs.extend(hx_logs)
                            updates.extend(hx_updates)
                            
                    elif "PULL" in logic_tag:
                        dx = 1 if tx < char.x else (-1 if tx > char.x else 0)
                        dy = 1 if ty < char.y else (-1 if ty > char.y else 0)
                        nx, ny = target.x + dx, target.y + dy
                        if not any(c.x == nx and c.y == ny for c in self.combatants) and (nx, ny) not in self.walls:
                            target.x, target.y = nx, ny
                            updates.append({"type": "MOVE_TOKEN", "id": target.id, "pos": [nx, ny]})
                            logs.append(f"{target.name} is dragged closer!")
                            hx_logs, hx_updates = self.check_tile_effects(target)
                            logs.extend(hx_logs)
                            updates.extend(hx_updates)
                            
                elif logic_tag.startswith("UTILITY:HEAL"): # Assuming a generic heal tag exists or is planned
                     heal = spell_data.get("tier", 1) * 10
                     target.hp = min(target.max_hp, target.hp + heal)
                     logs.append(f"{char.name} heals {target.name} for {heal} HP!")
                     updates.append({"type": "FCT", "text": f"+{heal} HEAL", "pos": [tx, ty], "style": "heal"})
                else:
                    # Generic hit for unimplemented logic tags
                    logs.append(f"{char.name} casts {orig_skill_name} on {target.name}! (Effect pending implementation)")
            else:
                logs.append(f"{char.name} casts {orig_skill_name} at the ground.")
                
            return " ".join(logs), updates
        # ------------------------------------------------------------------

        # ------------------------------------------------------------------
        # --- GENERIC QUADRANT SKILL RESOLUTION (Phase 48) ---
        # ------------------------------------------------------------------
        # Lazy load skills_v2
        if not getattr(self, "_quadrant_skills", None):
            matrix_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "skills_v2.json")
            try:
                with open(matrix_path, 'r', encoding='utf-8') as f:
                    self._quadrant_skills = json.load(f)
            except Exception as ex:
                self._quadrant_skills = {}
                
        # Search for skill across all 4 Quadrants
        q_skill_data = None
        quadrants = ["quadrant_1_violence", "quadrant_2_survival", "quadrant_3_influence", "quadrant_4_resolve"]
        for quad in quadrants:
            for s in self._quadrant_skills.get(quad, {}).get("skills", []):
                if s["name"].upper() == skill_name:
                    q_skill_data = s
                    q_skill_data["_quadrant"] = quad
                    break
            if q_skill_data: break
            
        if q_skill_data:
            quadrant = q_skill_data.get("_quadrant")
            sp_cost = 3 # Fixed SP cost for mundane physical skills for now
            if char.sp < sp_cost: 
                return f"Not enough SP for {orig_skill_name}! (Requires {sp_cost})", []
            
            # Action Mapping based on Quadrant Intent
            if quadrant == "quadrant_1_violence":
                # Melee/Ranged Attacks
                dist = max(abs(char.x - tx), abs(char.y - ty))
                max_range = 1 + h_bonus 
                if "MARKSMAN" in skill_name or "SKIRMISHER" in skill_name: max_range = 5 + h_bonus
                if dist > max_range: return f"Target out of range ({max_range} tiles).", []
                
                char.sp -= sp_cost
                target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
                if max_range > 1:
                     updates.append({"type": "PROJECTILE", "from": [char.x, char.y], "to": [tx, ty], "color": "#a8a29e"}) # grey arrow/thrown arc
                
                if target:
                    dmg = 8
                    final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, "IMPACT")
                    logs.extend(d_logs)
                    updates.extend(d_updates)
                    if "hero" in char.tags and "hero" not in target.tags:
                        self.apply_threat(target, char, final_dmg)
                    logs.append(f"{char.name} executes {orig_skill_name} on {target.name}! ({final_dmg} Physical DMG)")
                    updates.append({"type": "FCT", "text": f"-{final_dmg} IMPACT", "pos": [tx, ty], "style": "dmg"})
                    
                    if "BREAKER" in skill_name:
                        updates.append({"type": "SHAKE", "intensity": 4})
                else:
                    if "BREAKER" in skill_name and (tx, ty) in self.walls:
                        char.sp -= sp_cost
                        self.walls.remove((tx, ty))
                        if self.grid_cells: self.grid_cells[ty][tx] = 129
                        updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                        logs.append(f"{char.name} uses {orig_skill_name} and shatters the obstacle!")
                        updates.append({"type": "FCT", "text": "SHATTERED", "pos": [tx, ty], "style": "crit"})
                        updates.append({"type": "SHAKE", "intensity": 8})
                    elif max_range > 1: logs.append(f"{char.name} misses their shot.")
                    else: logs.append(f"{char.name} strikes the air.")

            elif quadrant == "quadrant_2_survival":
                 # Movement, defense, repositioning
                 if "SPRINTER" in skill_name or "ATHLETE" in skill_name:
                     if not hasattr(char, "temp_buffs"): char.temp_buffs = []
                     char.temp_buffs.append({"type": f"{orig_skill_name}_SPEED", "stat": "Reflexes", "bonus": 5, "duration": 2})
                     char.sp -= sp_cost
                     logs.append(f"{char.name} uses {orig_skill_name}! (+5 Reflexes for 2 rounds)")
                     updates.append({"type": "FCT", "text": "MOBILITY UP", "pos": [char.x, char.y], "style": "react"})
                 elif "VANGUARD" in skill_name or "DEFLECTOR" in skill_name:
                     if not hasattr(char, "status_effects"): char.status_effects = []
                     char.status_effects.append({"type": "RESIST_PHYSICAL", "duration": 2})
                     char.sp -= sp_cost
                     logs.append(f"{char.name} holds the line with {orig_skill_name}!")
                     updates.append({"type": "FCT", "text": "GUARDING", "pos": [char.x, char.y], "style": "heal"})
                 else:
                     logs.append(f"{orig_skill_name} logic pending.")
                     
            elif quadrant == "quadrant_3_influence":
                # Taunts, fears, debuffs
                char.sp -= sp_cost
                if "INTIMIDATOR" in skill_name or "COMMANDER" in skill_name:
                    updates.append({"type": "AOE_PULSE", "pos": [char.x, char.y], "radius": 3, "color": "#eab308"}) # Yellow aura
                    for c in self.combatants:
                        if "hero" not in c.tags and max(abs(char.x - c.x), abs(char.y - c.y)) <= 3:
                            current_max = max(self.threat.get(c.id, {}).values()) if self.threat.get(c.id) else 0
                            self.apply_threat(c, char, current_max + 10)
                            logs.append(f"{c.name}'s attention is drawn by {orig_skill_name}!")
                            updates.append({"type": "FCT", "text": "THREATENED", "pos": [c.x, c.y], "style": "dmg"})
                    logs.append(f"{char.name} uses {orig_skill_name} to control the battlefield!")
                else:
                    logs.append(f"{orig_skill_name} logic pending.")

            elif quadrant == "quadrant_4_resolve":
                 # Focus, Willpower, steady aim
                 if "MEDIC" in skill_name:
                     dist = max(abs(char.x - tx), abs(char.y - ty))
                     if dist > 1: return "Must be adjacent to use Medical skills.", []
                     target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
                     if target:
                         char.sp -= sp_cost
                         heal = 12
                         target.hp = min(target.max_hp, target.hp + heal)
                         logs.append(f"{char.name} applies first aid with {orig_skill_name} to {target.name}! (+{heal} HP)")
                         updates.append({"type": "FCT", "text": f"+{heal} MENDED", "pos": [tx, ty], "style": "heal"})
                     else: logs.append("No patient there.")
                 else:
                     if not hasattr(char, "temp_buffs"): char.temp_buffs = []
                     char.temp_buffs.append({"type": f"{orig_skill_name}_FOCUS", "stat": "Willpower", "bonus": 5, "duration": 2})
                     char.sp -= sp_cost
                     logs.append(f"{char.name} steels their resolve with {orig_skill_name}! (+5 Willpower)")
                     updates.append({"type": "FCT", "text": "FOCUSED", "pos": [char.x, char.y], "style": "react"})

            return " ".join(logs), updates
        # ------------------------------------------------------------------

        if skill_name == "ACID SPIT":
            sp_cost = 4
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            max_range = 5 + h_bonus
            if dist > max_range: return f"Target out of range ({max_range} tiles).", []
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            updates.append({"type": "PROJECTILE", "from": [char.x, char.y], "to": [tx, ty], "color": "#84cc16"})
            if target:
                dmg = 10
                final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, "ACID")
                logs.extend(d_logs)
                updates.extend(d_updates)
                
                if "hero" in char.tags and "hero" not in target.tags:
                    self.apply_threat(target, char, final_dmg)
                
                logs.append(f"{char.name} spits acid at {target.name}! ({final_dmg} DMG)")
                updates.append({"type": "FCT", "text": f"-{final_dmg} ACID", "pos": [tx, ty], "style": "dmg"})
            else: logs.append(f"{char.name} spits acid at the ground.")

        elif skill_name == "FLAME SPIT":
            sp_cost = 4
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            max_range = 5 + h_bonus
            if dist > max_range: return f"Target out of range ({max_range} tiles).", []
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            updates.append({"type": "PROJECTILE", "from": [char.x, char.y], "to": [tx, ty], "color": "#ef4444"})
            if target:
                dmg = 10
                final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, "HEAT")
                logs.extend(d_logs)
                updates.extend(d_updates)
                
                if "hero" in char.tags and "hero" not in target.tags:
                    self.apply_threat(target, char, final_dmg / 2)
                
                logs.append(f"{char.name} spits fire at {target.name}! ({final_dmg} DMG)")
                updates.append({"type": "FCT", "text": f"-{final_dmg} FIRE", "pos": [tx, ty], "style": "dmg"})
            else: logs.append(f"{char.name} spits fire at the ground.")

        elif skill_name == "SHOCKING BURST":
            sp_cost = 6
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            char.sp -= sp_cost
            updates.append({"type": "AOE_PULSE", "pos": [char.x, char.y], "radius": 2, "color": "#60a5fa"})
            for c in self.combatants:
                if c == char: continue
                if max(abs(char.x - c.x), abs(char.y - c.y)) <= 2:
                    dmg = 8
                    final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(c, dmg, "HEAT") # Shock is Heat-adjacent
                    logs.extend(d_logs)
                    updates.extend(d_updates)
                    if "hero" in char.tags and "hero" not in c.tags:
                        self.apply_threat(c, char, final_dmg)
                    logs.append(f"{c.name} is shocked!")
                    updates.append({"type": "FCT", "text": f"-{final_dmg} SHOCK", "pos": [c.x, c.y], "style": "crit"})
            to_remove = [w for w in self.walls if max(abs(char.x - w[0]), abs(char.y - w[1])) <= 2]
            for w in to_remove:
                self.walls.remove(w)
                if self.grid_cells: self.grid_cells[w[1]][w[0]] = 129
                updates.append({"type": "GRID_UPDATE", "x": w[0], "y": w[1], "cell": 128})
                logs.append("A nearby wall crumbles!")

        elif skill_name == "GRAPPLING LASH":
            sp_cost = 5
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            max_range = 4 + h_bonus
            if dist > max_range: return f"Target out of range ({max_range} tiles).", []
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            if target:
                dx = 1 if tx < char.x else (-1 if tx > char.x else 0)
                dy = 1 if ty < char.y else (-1 if ty > char.y else 0)
                nx, ny = char.x + dx, char.y + dy
                if not any(c.x == nx and c.y == ny for c in self.combatants) and (nx, ny) not in self.walls:
                    target.x, target.y = nx, ny
                    if "hero" in char.tags and "hero" not in target.tags:
                        self.apply_threat(target, char, 5) # Minor threat for dragging
                    logs.append(f"{char.name} drags {target.name} close!")
                    updates.append({"type": "FCT", "text": "DRAGGED", "pos": [nx, ny], "style": "react"})
                    hx_logs, hx_updates = self.check_tile_effects(target)
                    logs.extend(hx_logs)
                    updates.extend(hx_updates)
                else: logs.append(f"{target.name} can't be pulled there.")
            else: logs.append("Lash strikes nothing.")

        elif skill_name == "PRIMAL FURY":
            sp_cost = 5
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            char.sp -= sp_cost
            if not hasattr(char, "status_effects"): char.status_effects = []
            char.status_effects.append({"type": "ENRAGED", "duration": 3})
            logs.append(f"{char.name} enters a PRIMAL FURY!")
            updates.append({"type": "FCT", "text": "ENRAGED", "pos": [char.x, char.y], "style": "crit"})
            updates.append({"type": "SHAKE", "intensity": 5})

        elif skill_name == "REJUVENATING SPORES":
            sp_cost = 5
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            if dist > 3: return "Target out of range (3 tiles).", []
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            updates.append({"type": "PROJECTILE", "from": [char.x, char.y], "to": [tx, ty], "color": "#f472b6"}) # Pink spores
            if target:
                heal = 15
                target.hp = min(target.max_hp, target.hp + heal)
                logs.append(f"{char.name} releases spores onto {target.name}! (+{heal} HP)")
                updates.append({"type": "FCT", "text": f"+{heal} HEAL", "pos": [tx, ty], "style": "react"})
            else: logs.append(f"{char.name} releases spores into the empty air.")

        elif skill_name == "TAUNTING ROAR":
            sp_cost = 4
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            char.sp -= sp_cost
            updates.append({"type": "AOE_PULSE", "pos": [char.x, char.y], "radius": 3, "color": "#ef4444"})
            for c in self.combatants:
                if "hero" not in c.tags and max(abs(char.x - c.x), abs(char.y - c.y)) <= 3:
                    # Force maximum threat
                    current_max = max(self.threat.get(c.id, {}).values()) if self.threat.get(c.id) else 0
                    self.apply_threat(c, char, current_max + 10)
                    logs.append(f"{c.name} is enraged by {char.name}!")
                    updates.append({"type": "FCT", "text": "ENRAGED", "pos": [c.x, c.y], "style": "dmg"})
            updates.append({"type": "SHAKE", "intensity": 5})
            logs.append(f"{char.name} lets out a biological roar!")

        elif skill_name == "KINETIC SHOVE":
            sp_cost = 4
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            if dist > 1: return "Must be adjacent to shove!", []
            char.sp -= sp_cost
            target = next((c for c in self.combatants if c.x == tx and c.y == ty), None)
            if not target: return "No one there to shove.", []
            
            dx = tx - char.x
            dy = ty - char.y
            
            # Push 2 tiles
            push_dist = 2
            curr_x, curr_y = tx, ty
            actual_push = 0
            
            for _ in range(push_dist):
                nx, ny = curr_x + dx, curr_y + dy
                if not (0 <= nx < self.cols and 0 <= ny < self.rows) or (nx, ny) in self.walls:
                    # Wall Slam
                    final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, 5, "IMPACT")
                    logs.extend(d_logs)
                    updates.extend(d_updates)
                    logs.append(f"{target.name} SLAMS into a wall! (+{final_dmg} Impact DMG)")
                    updates.append({"type": "FCT", "text": "WALL SLAM", "pos": [curr_x, curr_y], "style": "dmg"})
                    break
                # Occupied by another entity? Stop shove but maybe bump them?
                if any(c.x == nx and c.y == ny for c in self.combatants if c.hp > 0):
                    break
                
                curr_x, curr_y = nx, ny
                actual_push += 1
            
            # Check elevation change (Falling damage)
            start_h = self.elevation.get((tx, ty), 0)
            end_h = self.elevation.get((curr_x, curr_y), 0)
            if end_h < start_h:
                h_diff = start_h - end_h
                fall_dmg = h_diff * 10
                final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, fall_dmg, "IMPACT")
                logs.extend(d_logs)
                updates.extend(d_updates)
                logs.append(f"{target.name} falls {h_diff} levels! (-{final_dmg} HP)")
                updates.append({"type": "FCT", "text": f"-{final_dmg} FALL", "pos": [curr_x, curr_y], "style": "dmg"})

            target.x, target.y = curr_x, curr_y
            logs.append(f"{char.name} SHOVES {target.name} back {actual_push} tiles!")
            updates.append({"type": "MOVE_TOKEN", "id": target.id, "pos": [curr_x, curr_y]})
            
            # Immediate hazard check
            hx_logs, hx_updates = self.check_tile_effects(target)
            logs.extend(hx_logs)
            updates.extend(hx_updates)

            if "hero" in char.tags and "hero" not in target.tags:
                self.apply_threat(target, char, 5) # Minor threat for shoving

        elif skill_name == "JUMP":
            sp_cost = 3
            if char.sp < sp_cost: return f"Not enough SP for {skill_name}!", []
            dist = max(abs(char.x - tx), abs(char.y - ty))
            if dist > 3: return "Jump range is 3 tiles!", []
            if (tx, ty) == (char.x, char.y): return "Already there.", []
            
            # Destination check
            if (tx, ty) in self.walls: return "Cannot jump into a wall.", []
            if any(c.x == tx and c.y == ty for c in self.combatants if c.hp > 0):
                return "Destination is occupied.", []

            char.sp -= sp_cost
            updates.append({"type": "JUMP", "id": char.id, "from": [char.x, char.y], "to": [tx, ty]})
            
            char.x, char.y = tx, ty
            logs.append(f"{char.name} JUMPS to {tx}, {ty}!")
            updates.append({"type": "MOVE_TOKEN", "id": char.id, "pos": [tx, ty]})
            
            # Immediate hazard check at DESTINATION ONLY
            hx_logs, hx_updates = self.check_tile_effects(char)
            logs.extend(hx_logs)
            updates.extend(hx_updates)

        return " ".join(logs) if logs else "Ability failed.", updates

    def apply_threat(self, npc: Entity, source: Entity, ammount: float):
        if npc.id not in self.threat: self.threat[npc.id] = {}
        self.threat[npc.id][source.id] = self.threat[npc.id].get(source.id, 0) + ammount

    def process_dynamic_hazards(self):
        """Hazards like ACID and LAVA spread each round."""
        logs = []
        updates = []
        new_hazards = {}
        
        hazard_types = ["ACID", "LAVA"]
        for (x, y), h_type in self.terrain.items():
            if h_type not in hazard_types: continue
            
            spread_chance = 0.25 if h_type == "ACID" else 0.10
            if random.random() < spread_chance:
                dx, dy = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.walls:
                    target_terrain = self.terrain.get((nx, ny))
                    if target_terrain is None or target_terrain == "DIFFICULT":
                        new_hazards[(nx, ny)] = h_type
                        if target_terrain == "DIFFICULT":
                            logs.append(f"The {h_type.lower()} dissolves a nearby bush!")
                        updates.append({"type": "GRID_UPDATE", "x": nx, "y": ny, "cell": 131 if h_type == "ACID" else 132})
                        
        for pos, h_type in new_hazards.items():
            self.terrain[pos] = h_type
            # Clear items if lava spreads
            if h_type == "LAVA" and pos in self.items:
                del self.items[pos]
                updates.append({"type": "ITEM_PICKUP", "x": pos[0], "y": pos[1]}) # Visual removal
                
        return logs, updates

    def check_tile_effects(self, char: Entity):
        """Processes hazards AND items when entering a tile."""
        logs = []
        updates = []
        
        # 1. Check Hazards
        t_type = self.terrain.get((char.x, char.y))
        if t_type == "ACID":
            dmg = 5
            final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(char, dmg, "ACID")
            logs.extend(d_logs)
            updates.extend(d_updates)
            logs.append(f"{char.name} sizzles in the acid pit! (-{final_dmg} HP)")
            updates.append({"type": "FCT", "text": f"-{final_dmg} ACID", "pos": [char.x, char.y], "style": "dmg"})
        elif t_type == "LAVA":
            dmg = 10
            final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(char, dmg, "HEAT")
            logs.extend(d_logs)
            updates.extend(d_updates)
            logs.append(f"{char.name} is scorched by lava! (-{final_dmg} HP)")
            updates.append({"type": "FCT", "text": f"-{final_dmg} LAVA", "pos": [char.x, char.y], "style": "crit"})
            updates.append({"type": "SHAKE", "intensity": 3})
        elif t_type == "POISON":
            if not hasattr(char, "status_effects"): char.status_effects = []
            if not any(s["type"] == "POISON" for s in char.status_effects):
                char.status_effects.append({"type": "POISON", "duration": 3, "dmg": 2})
                logs.append(f"{char.name} inhales poisonous spores!")
                updates.append({"type": "FCT", "text": "POISONED", "pos": [char.x, char.y], "style": "react"})
        elif t_type == "GOO":
            if char.sp >= 2:
                char.sp -= 2
                logs.append(f"{char.name} struggles in the Goo! (-2 SP Sluggish)")
                updates.append({"type": "FCT", "text": "-2 SP GOO", "pos": [char.x, char.y], "style": "react"})
        
        # 2. Check Items
        i_type = self.items.get((char.x, char.y))
        if i_type:
            if not hasattr(char, "temp_buffs"): char.temp_buffs = []
            if i_type == "MIGHT_VIAL":
                char.temp_buffs.append({"type": "MIGHT_VIAL", "stat": "Might", "bonus": 5, "duration": 3})
                logs.append(f"{char.name} consumes an Evolution Vial! (+5 Might for 3 rounds)")
                updates.append({"type": "FCT", "text": "MIGHT UP!", "pos": [char.x, char.y], "style": "react"})
            elif i_type == "SPEED_VIAL":
                char.temp_buffs.append({"type": "SPEED_VIAL", "stat": "Reflexes", "bonus": 5, "duration": 3})
                logs.append(f"{char.name} consumes a Speed Vial! (+5 Reflexes for 3 rounds)")
                updates.append({"type": "FCT", "text": "SPEED UP!", "pos": [char.x, char.y], "style": "react"})
            elif i_type == "BIOMASS":
                heal = 15
                char.hp = min(char.max_hp, char.hp + heal)
                logs.append(f"{char.name} consumes raw biomass! (+15 HP)")
                updates.append({"type": "FCT", "text": "+15 HP", "pos": [char.x, char.y], "style": "react"})
            
            del self.items[(char.x, char.y)]
            updates.append({"type": "ITEM_PICKUP", "x": char.x, "y": char.y})
            
        return logs, updates

    def get_highest_threat_target(self, npc: Entity):
        """Returns the combatant with the highest threat to this NPC."""
        threat_map = self.threat.get(npc.id, {})
        if not threat_map:
            # Fallback to nearest hero if no threat recorded
            hero = next((c for c in self.combatants if "hero" in c.tags), None)
            return hero
            
        # Filter for living combatants
        living_targets = [c for c in self.combatants if c.id in threat_map and c.hp > 0]
        if not living_targets:
            hero = next((c for c in self.combatants if "hero" in c.tags), None)
            return hero
            
        # Find target with highest threat
        return max(living_targets, key=lambda c: threat_map.get(c.id, 0))

    def get_tile_danger_score(self, x: int, y: int) -> int:
        """Returns a danger rating for AI pathfinding and evaluation."""
        t = self.terrain.get((x, y))
        if t == "LAVA": return 10
        if t == "ACID": return 5
        if t == "STEAM_VENT": return 4
        if t == "GOO": return 2
        return 0

    def run_ai_turn(self):
        """Processes AI combatants and gathers visual updates."""
        self.pending_updates = []
        npcs = [c for c in self.combatants if "hero" not in c.tags and c.hp > 0]
        
        for npc in npcs:
            self.pending_updates.append({"type": "ACTION_START", "id": npc.id})
            
            # 0. Hazard Avoidance (Get off active hazards if possible)
            curr_hazard = self.terrain.get((npc.x, npc.y))
            if curr_hazard in ["LAVA", "ACID", "STEAM_VENT"] and npc.sp >= 1:
                escape_dirs = [(-1,0), (1,0), (0,-1), (0,1)]
                random.shuffle(escape_dirs)
                for dx, dy in escape_dirs:
                    nx, ny = npc.x + dx, npc.y + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.walls:
                        if self.terrain.get((nx, ny)) not in ["LAVA", "ACID", "STEAM_VENT"]:
                            npc.x, npc.y = nx, ny
                            self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                            # No log for move-avoidance to keep it clean
                            break

            # Select target based on Threat
            target = self.get_highest_threat_target(npc)
            if not target: continue
            
            dist = max(abs(npc.x - target.x), abs(npc.y - target.y))
            archetype = getattr(npc, "metadata", {}).get("Archetype", "MELEE").upper()
            
            npc_spells = getattr(npc, "metadata", {}).get("Spells", [])
            npc_skills = getattr(npc, "metadata", {}).get("Skills", [])
            
            executed = False
            
            # --- SNIPER LOGIC ---
            if archetype == "SNIPER":
                if dist < 4 and npc.sp >= 1:
                    escape_dirs = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
                    random.shuffle(escape_dirs)
                    for dx, dy in escape_dirs:
                        nx, ny = npc.x + dx, npc.y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.walls:
                            new_dist = max(abs(nx - target.x), abs(ny - target.y))
                            if new_dist > dist:
                                npc.x, npc.y = nx, ny
                                self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                                hx_logs, hx_updates = self.check_tile_effects(npc)
                                self.replay_log.extend(hx_logs)
                                self.pending_updates.extend(hx_updates)
                                executed = True
                                break
                
                if not executed:
                    h_bonus = self.elevation.get((npc.x, npc.y), 0) - self.elevation.get((target.x, target.y), 0)
                    if dist <= 5 + max(0, h_bonus):
                        skill_to_use = None
                        if any("MARKSMAN" in s for s in npc_skills):
                            skill_to_use = next(s for s in npc_skills if "MARKSMAN" in s)
                        elif npc_spells:
                            skill_to_use = npc_spells[0]
                        else:
                            # Combo Logic Fallback
                            t_terrain = self.terrain.get((target.x, target.y))
                            skill_to_use = "FLAME SPIT" if t_terrain == "GOO" else "ACID SPIT"
                        
                        log_msg, skill_updates = self.use_skill(npc, skill_to_use, target.x, target.y)
                        if not log_msg.startswith("Not enough SP") and "failed" not in log_msg.lower():
                            self.replay_log.append(log_msg)
                            self.pending_updates.extend(skill_updates)
                            executed = True

            # --- HEALER LOGIC ---
            elif archetype == "HEALER":
                wounded = sorted([c for c in npcs if c.hp < c.max_hp], key=lambda c: c.hp / c.max_hp)
                if wounded:
                    w_target = wounded[0]
                    t_dist = max(abs(npc.x - w_target.x), abs(npc.y - w_target.y))
                    skill_to_use = None
                    opt_range = 1
                    if any("MEDIC" in s for s in npc_skills):
                        skill_to_use = next(s for s in npc_skills if "MEDIC" in s)
                        opt_range = 1
                    else:
                        skill_to_use = "REJUVENATING SPORES"
                        opt_range = 3
                        
                    if t_dist <= opt_range:
                        log_msg, skill_updates = self.use_skill(npc, skill_to_use, w_target.x, w_target.y)
                        if not log_msg.startswith("Not enough SP") and "failed" not in log_msg.lower():
                            self.replay_log.append(log_msg)
                            self.pending_updates.extend(skill_updates)
                            executed = True
                            
                    if not executed and npc.sp >= 1:
                        path = self.find_path((npc.x, npc.y), (w_target.x, w_target.y))
                        if path and len(path) > 1:
                            tx, ty = path[0]
                            if not any(c.x == tx and c.y == ty for c in self.combatants if c.hp > 0):
                                npc.x, npc.y = tx, ty
                                self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                                hx_logs, hx_updates = self.check_tile_effects(npc)
                                self.replay_log.extend(hx_logs)
                                self.pending_updates.extend(hx_updates)
                                executed = True
                
                if not executed and dist < 3 and npc.sp >= 1:
                    escape_dirs = [(-1,0), (1,0), (0,-1), (0,1)]
                    random.shuffle(escape_dirs)
                    for dx, dy in escape_dirs:
                        nx, ny = npc.x + dx, npc.y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.walls:
                            if max(abs(nx-target.x), abs(ny-target.y)) > dist:
                                npc.x, npc.y = nx, ny
                                self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                                executed = True
                                break

            # --- DEFAULT MELEE/ALPHA LOGIC ---
            if not executed:
                # 1. Strategic Shove (High Priority)
                might = self.get_effective_stat(npc, "Might")
                if dist == 1 and might >= 12 and npc.sp >= 4:
                    dx, dy = target.x - npc.x, target.y - npc.y
                    # Check 1 or 2 tiles behind target
                    for push_len in [1, 2]:
                        px, py = target.x + (dx * push_len), target.y + (dy * push_len)
                        if self.get_tile_danger_score(px, py) >= 4:
                            log_msg, skill_updates = self.use_skill(npc, "KINETIC SHOVE", target.x, target.y)
                            self.replay_log.append(f"[STRATEGY] {npc.name} attempts to shove {target.name} into the hazard!")
                            self.replay_log.append(log_msg)
                            self.pending_updates.extend(skill_updates)
                            executed = True
                            break

                if not executed:
                    if dist <= 1:
                        skill_to_use = None
                        if npc_spells:
                            skill_to_use = npc_spells[0]
                        elif npc_skills:
                            skill_to_use = npc_skills[0]
                            
                        if skill_to_use:
                            log_msg, skill_updates = self.use_skill(npc, skill_to_use, target.x, target.y)
                            if not log_msg.startswith("Not enough SP") and "failed" not in log_msg.lower() and "range" not in log_msg.lower():
                                self.replay_log.append(log_msg)
                                self.pending_updates.extend(skill_updates)
                                executed = True
                                
                        if not executed:
                            results, v_updates = self.attack_target(npc, target)
                            self.replay_log.extend(results)
                            self.pending_updates.extend(v_updates)
                            executed = True
                    elif npc.sp >= 1:
                        path = self.find_path((npc.x, npc.y), (target.x, target.y))
                        if path and len(path) > 1:
                            tx, ty = path[0]
                            occupied = any(c.x == tx and c.y == ty for c in self.combatants if c.hp > 0)
                            if not occupied:
                                npc.x, npc.y = tx, ty
                                self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                                hx_logs, hx_updates = self.check_tile_effects(npc)
                                self.replay_log.extend(hx_logs)
                                self.pending_updates.extend(hx_updates)
                            else:
                                # Surround logic
                                adj = []
                                for dx in [-1,0,1]:
                                    for dy in [-1,0,1]:
                                        if dx==0 and dy==0: continue
                                        nx, ny = target.x + dx, target.y + dy
                                        if not any(c.x == nx and c.y == ny for c in self.combatants if c.hp > 0) and (nx, ny) not in self.walls:
                                            adj.append((nx, ny))
                                if adj:
                                    best_spot = min(adj, key=lambda p: max(abs(npc.x - p[0]), abs(npc.y - p[1])))
                                    path_alt = self.find_path((npc.x, npc.y), best_spot)
                                    if path_alt:
                                        tx, ty = path_alt[0]
                                        if not any(c.x == tx and c.y == ty for c in self.combatants if c.hp > 0):
                                            npc.x, npc.y = tx, ty
                                            self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
                                            hx_logs, hx_updates = self.check_tile_effects(npc)
                                            self.replay_log.extend(hx_logs)
                                            self.pending_updates.extend(hx_updates)
                else:
                    npc.sp += 5
                    self.pending_updates.append({"type": "FCT", "text": "RESTING...", "pos": [npc.x, npc.y], "style": "miss"})
            
            self.pending_updates.append({"type": "UPDATE_HP", "id": target.id, "hp": target.hp})
            self.pending_updates.append({"type": "UPDATE_HP", "id": npc.id, "hp": npc.hp})

    def end_round(self):
        """Regenerate SP and process end-of-round DOT/Hazards/Buffs."""
        self.round_count += 1
        self.reactions_used.clear()
        logs = [f"--- Round {self.round_count} Begins ---"]
        updates = []
        
        # Hazard Expansion
        h_logs, h_updates = self.process_dynamic_hazards()
        logs.extend(h_logs)
        updates.extend(h_updates)
        
        # 1. Process Pheromone Synthesis (Pack Leaders)
        for c in self.combatants:
            if c.hp <= 0: continue
            traits = getattr(c, 'metadata', {}).get("Traits", {})
            if "Pheromone Synthesis" in traits:
                updates.append({"type": "AOE_PULSE", "pos": [c.x, c.y], "radius": 3, "color": "#22c55e", "alpha": 0.3})
                for ally in self.combatants:
                    if ally.hp > 0 and (("hero" in c.tags) == ("hero" in ally.tags)):
                        dist = max(abs(c.x - ally.x), abs(c.y - ally.y))
                        if dist <= 3:
                            if not hasattr(ally, "status_effects"): ally.status_effects = []
                            if not any(s["type"] == "PHEROMONES" for s in ally.status_effects):
                                ally.status_effects.append({"type": "PHEROMONES", "duration": 1})
                                updates.append({"type": "FCT", "text": "PHEROMONES", "pos": [ally.x, ally.y], "style": "react"})

        # 2. Process Boss Phases (Evolutionary Overlord)
        for c in self.combatants:
            if c.hp <= 0: continue
            if "boss" in c.tags:
                # Shedding Phase (50% HP)
                if c.hp <= c.max_hp * 0.5 and not getattr(c, "has_shed", False):
                    c.has_shed = True
                    if not hasattr(c, "status_effects"): c.status_effects = []
                    c.status_effects.append({"type": "REGENERATION", "duration": 999})
                    logs.append(f"[BOSS] {c.name} sheds its outer carapace! It is regenerating!")
                    updates.append({"type": "AOE_PULSE", "pos": [c.x, c.y], "radius": 5, "color": "#f87171", "alpha": 0.5})
                    updates.append({"type": "FCT", "text": "SHEDDING", "pos": [c.x, c.y], "style": "crit"})
                    # Immediate Pheromone Pulse
                    for ally in self.combatants:
                        if ally.hp > 0 and (("hero" in c.tags) == ("hero" in ally.tags)):
                            dist = max(abs(c.x - ally.x), abs(c.y - ally.y))
                            if dist <= 5:
                                if not hasattr(ally, "status_effects"): ally.status_effects = []
                                ally.status_effects.append({"type": "PHEROMONES", "duration": 3})

        # 3. Process Steam Vents (Random Activation)
        import random
        for (pos_str, h_type) in self.terrain.items():
            if h_type == "STEAM_VENT" and random.random() < 0.3:
                tx, ty = map(int, pos_str.split(","))
                updates.append({"type": "AOE_PULSE", "pos": [tx, ty], "radius": 1, "color": "#ffffff", "alpha": 0.8})
                target = next((c for c in self.combatants if c.x == tx and c.y == ty and c.hp > 0), None)
                if target:
                    dmg = 5
                    target.take_damage(dmg)
                    logs.append(f"[HAZARD] Steam Vent erupts under {target.name}! (-5 HP)")
                    updates.append({"type": "FCT", "text": "-5 STEAM", "pos": [tx, ty], "style": "dmg"})
                    # SHOVE Logic
                    dirs = [[0,1], [0,-1], [1,0], [-1,0]]
                    random.shuffle(dirs)
                    for dx, dy in dirs:
                        nx, ny = target.x + dx, target.y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid_cells[ny][nx] != 896:
                            target.x, target.y = nx, ny
                            logs.append(f"[SHOVE] {target.name} is blasted to {nx}, {ny}!")
                            updates.append({"type": "MOVE", "id": target.id, "pos": [nx, ny]})
                            break

        for c in self.combatants:
            if c.hp <= 0: continue
            c.sp = min(c.max_sp, c.sp + 5)
            
            hx_logs, hx_updates = self.check_tile_effects(c)
            logs.extend(hx_logs)
            updates.extend(hx_updates)
            
            if hasattr(c, "status_effects"):
                active_effects = []
                for s in c.status_effects:
                    if s["type"] == "POISON":
                        final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(c, s["dmg"], "ACID") # Poison is acid-type
                        logs.extend(d_logs)
                        logs.append(f"{c.name} suffers from {s['type']}! (-{final_dmg} HP)")
                        updates.append({"type": "FCT", "text": f"-{final_dmg} {s['type']}", "pos": [c.x, c.y], "style": "dmg"})
                    
                    if s["type"] == "REGENERATION":
                        heal = 5
                        c.hp = min(c.max_hp, c.hp + heal)
                        logs.append(f"{c.name} regenerates {heal} HP.")
                        updates.append({"type": "FCT", "text": f"+{heal} REGEN", "pos": [c.x, c.y], "style": "heal"})
                        updates.append({"type": "UPDATE_HP", "id": c.id, "hp": c.hp})
                    
                    s["duration"] -= 1
                    if s["duration"] > 0: active_effects.append(s)
                    else:
                        logs.append(f"{c.name} is no longer {s['type']}.")
                c.status_effects = active_effects
            
            if hasattr(c, "temp_buffs"):
                active_buffs = []
                for b in c.temp_buffs:
                    b["duration"] -= 1
                    if b["duration"] > 0: 
                        active_buffs.append(b)
                    else:
                        logs.append(f"{c.name}'s {b['stat']} buff has expired.")
                        updates.append({"type": "FCT", "text": f"{b['stat']} EXPIRED", "pos": [c.x, c.y], "style": "miss"})
                c.temp_buffs = active_buffs
            
            updates.append({"type": "UPDATE_HP", "id": c.id, "hp": c.hp})
            updates.append({"type": "UPDATE_SP", "id": c.id, "sp": c.sp})

        self.replay_log.extend(logs)
        self.pending_updates.extend(updates)

    def attack_target(self, attacker, target):
        logs = []
        v_updates = []
        context = {"def_bonus": 0, "force_miss": False, "atk_bonus": 0}
        
        # 1. Elevation Check (High Ground)
        atk_h = self.elevation.get((attacker.x, attacker.y), 0)
        def_h = self.elevation.get((target.x, target.y), 0)
        if atk_h > def_h:
            context["atk_bonus"] += 2
            logs.append(f"[HIGH GROUND] {attacker.name} strikes from above! (+2 Hit)")

        # 2. Cover Check (Bushes)
        dist = max(abs(attacker.x - target.x), abs(attacker.y - target.y))
        if dist > 1: # Ranged/Lash attack
            t_terrain = self.terrain.get((target.x, target.y))
            if t_terrain == "DIFFICULT":
                context["def_bonus"] += 5
                logs.append(f"[COVER] {target.name} is hidden in the brush! (+5 Defense)")

        # 3. Pack Tactics Check
        allies = [c for c in self.combatants if (("hero" in c.tags) == ("hero" in attacker.tags)) and c != attacker and c.hp > 0]
        for ally in allies:
            if max(abs(ally.x - target.x), abs(ally.y - target.y)) <= 1:
                context["atk_bonus"] += 2
                logs.append(f"[PACK TACTICS] {attacker.name} coordinates with {ally.name}! (+2 Hit)")
                break

        r_logs, r_updates = self.handle_reactions(attacker, target, "BEFORE_ATTACK", context)
        logs.extend(r_logs)
        v_updates.extend(r_updates)

        if attacker.sp < 2:
            v_updates.append({"type": "FCT", "text": "TIRED", "pos": [attacker.x, attacker.y], "style": "dmg"})
            return logs, v_updates
        attacker.sp -= 2
        
        atk_might = self.get_effective_stat(attacker, "Might") + context["atk_bonus"]
        def_reflex = self.get_effective_stat(target, "Reflexes") + context["def_bonus"]
        
        atk_roll = 1 if context["force_miss"] else random.randint(1, 20) + (atk_might // 2)
        def_roll = random.randint(1, 20) + (def_reflex // 2)
        margin = atk_roll - def_roll
        
        logs.append(f"{attacker.name} strikes {target.name}: {atk_roll} vs {def_roll}")
        
        # Enraged Damage Bonus
        e_bonus = 0
        if hasattr(attacker, "status_effects"):
            if any(s["type"] == "ENRAGED" for s in attacker.status_effects):
                e_bonus = 5
        
        if margin >= 10: 
            dmg = 15 + e_bonus
            final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, "IMPACT")
            logs.extend(d_logs)
            v_updates.extend(d_updates)
            
            if "hero" in attacker.tags and "hero" not in target.tags:
                self.apply_threat(target, attacker, final_dmg)
            v_updates.extend([{"type": "FCT", "text": f"-{final_dmg} HP!", "pos": [target.x, target.y], "style": "crit"}, {"type": "SHAKE", "intensity": 5}])
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs)
            v_updates.extend(dr_updates)
        elif margin > 0: 
            dmg = 8 + e_bonus
            final_dmg, d_logs, d_updates = self.apply_damage_with_resistance(target, dmg, "IMPACT")
            logs.extend(d_logs)
            v_updates.extend(d_updates)
            
            if "hero" in attacker.tags and "hero" not in target.tags:
                self.apply_threat(target, attacker, final_dmg)
            v_updates.append({"type": "FCT", "text": f"-{final_dmg}", "pos": [target.x, target.y], "style": "dmg"})
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs)
            v_updates.extend(dr_updates)
        else: v_updates.append({"type": "FCT", "text": "MISS", "pos": [target.x, target.y], "style": "miss"})
        
        # Check Enrage Threshold for target (Predators only)
        if "hero" not in target.tags and target.hp > 0 and target.hp <= target.max_hp * 0.3:
            if not any(s["type"] == "ENRAGED" for s in getattr(target, "status_effects", [])):
                if random.random() < 0.5:
                    if not hasattr(target, "status_effects"): target.status_effects = []
                    target.status_effects.append({"type": "ENRAGED", "duration": 2})
                    logs.append(f"{target.name} is enraged by their wounds!")
                    v_updates.append({"type": "FCT", "text": "PRIMAL FURY", "pos": [target.x, target.y], "style": "crit"})
                    v_updates.append({"type": "SHAKE", "intensity": 10})

        return logs, v_updates

    def move_char(self, char, tx, ty):
        if not (0 <= tx < self.cols and 0 <= ty < self.rows): return False, "Boundaries reached.", []
        if (tx, ty) in self.walls: return False, "Path blocked.", []
        moves = max(abs(char.x - tx), abs(char.y - ty))
        base_cost = 2 if self.terrain.get((tx, ty)) == "DIFFICULT" else 1
        sp_needed = moves * base_cost
        if char.sp < sp_needed: return False, f"Not enough SP! ({sp_needed} required)", []
        char.sp -= sp_needed
        char.x, char.y = tx, ty
        hx_logs, hx_updates = self.check_tile_effects(char)
        return True, f"Moved to {tx},{ty}.", hx_updates
