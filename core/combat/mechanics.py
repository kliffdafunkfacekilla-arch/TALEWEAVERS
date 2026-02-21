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
        self.terrain: Dict[tuple, str] = {} # (x, y) -> "DIFFICULT", etc.
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
                    if self.terrain.get(neighbor) == "DIFFICULT": move_cost = 2
                    
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
                    updates.append({"type": "UPDATE_HP", "id": player.id, "hp": player.hp}) # For recoil dmg
                    updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
            else:
                log = [f"Target {target_id} not found."]

        elif action == "MOVE":
            dx, dy = params.get("dx", 0), params.get("dy", 0)
            ok, msg = self.move_char(player, int(player.x + dx), int(player.y + dy))
            log = [msg]
            if ok: 
                updates.append({"type": "MOVE_TOKEN", "id": player.id, "pos": [player.x, player.y]})
                updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})
                
        elif action == "SMASH":
            tx, ty = params.get("x", 0), params.get("y", 0)
            ok, msg, smash_updates = self.smash_tile(player, tx, ty)
            log = [msg]
            updates.extend(smash_updates)
            if ok:
                updates.append({"type": "GRID_UPDATE", "x": tx, "y": ty, "cell": 128})
                updates.append({"type": "UPDATE_SP", "id": player.id, "sp": player.sp})

        return " ".join(log), updates

    def handle_reactions(self, source: Entity, target: Entity, trigger: str, context: Dict[str, Any]):
        """
        Processes Evolutionary Trait Reactions.
        Triggers: "BEFORE_ATTACK", "POST_DAMAGE"
        """
        logs = []
        v_updates = []
        
        traits = getattr(target, 'metadata', {}).get("Traits", {})
        target_stats = target.get_component(Stats)
        
        for name, mechanic in traits.items():
            # 1. Danger Sense (Reaction Dodge)
            if "danger sense" in name.lower() and trigger == "BEFORE_ATTACK":
                reaction_key = f"{target.id}_dangersense_{self.round_count}"
                if reaction_key not in self.reactions_used:
                    self.reactions_used.add(reaction_key)
                    bonus = 5
                    context["def_bonus"] = context.get("def_bonus", 0) + bonus
                    logs.append(f"[REACTION] {target.name}'s Danger Sense flares up! (+{bonus} Defense)")
                    v_updates.append({"type": "FCT", "text": "DANGER SENSE", "pos": [target.x, target.y], "style": "react"})

            # 2. Thorns / Spines (Damage Recoil)
            if ("thorns" in name.lower() or "spines" in name.lower()) and trigger == "POST_DAMAGE":
                recoil = 2
                source.hp -= recoil
                logs.append(f"[REACTION] {source.name} is pricked by {target.name}'s spines! ({recoil} Recoil DMG)")
                v_updates.append({"type": "FCT", "text": f"-{recoil} RECOIL", "pos": [source.x, source.y], "style": "dmg"})

            # 3. Reactive Camo (Forced Reroll / Blur)
            if "reactive camo" in name.lower() and trigger == "BEFORE_ATTACK":
                if random.random() < 0.25: # 25% chance
                    context["force_miss"] = True
                    logs.append(f"[REACTION] {target.name}'s Camo blurs their form!")
                    v_updates.append({"type": "FCT", "text": "BLURRED", "pos": [target.x, target.y], "style": "react"})

        return logs, v_updates

    def smash_tile(self, char, tx, ty):
        """Might-based environmental destruction."""
        if (tx, ty) not in self.walls:
            return False, "There is nothing robust to smash here.", []
            
        dist = max(abs(char.x - tx), abs(char.y - ty))
        if dist > 1:
            return False, "Target too far to smash.", []
            
        sp_cost = 3
        if char.sp < sp_cost:
            return False, f"Too exhausted to smash! (Need {sp_cost} SP)", []
            
        stats = char.get_component(Stats)
        might = stats.get("Might", 10) if stats else 10
        
        check = random.randint(1, 20) + (might // 2)
        threshold = 15
        char.sp -= sp_cost
        
        if check >= threshold:
            self.walls.remove((tx, ty))
            if self.grid_cells:
                self.grid_cells[ty][tx] = 129
            return True, f"{char.name} SMASHES the obstacle into rubble!", [{"type": "SHAKE", "intensity": 8}, {"type": "FCT", "text": "SMASH!", "pos": [tx, ty], "style": "crit"}]
        else:
            return False, f"{char.name} strikes the obstacle, but it holds firm.", [{"type": "FCT", "text": "CLANG", "pos": [tx, ty], "style": "dmg"}]

    def run_ai_turn(self):
        """Processes AI combatants and gathers visual updates."""
        hero = next((c for c in self.combatants if "hero" in c.tags), None)
        if not hero: return
        
        self.pending_updates = []
        
        for npc in [c for c in self.combatants if "hero" not in c.tags]:
            if npc.hp <= 0: continue
            dist = max(abs(npc.x - hero.x), abs(npc.y - hero.y))
            
            self.pending_updates.append({"type": "ACTION_START", "id": npc.id})

            if dist <= 1:
                results, v_updates = self.attack_target(npc, hero)
                self.replay_log.extend(results)
                self.pending_updates.extend(v_updates)
                self.pending_updates.append({"type": "UPDATE_HP", "id": hero.id, "hp": hero.hp})
                self.pending_updates.append({"type": "UPDATE_HP", "id": npc.id, "hp": npc.hp})
            elif npc.sp >= 1:
                path = self.find_path((npc.x, npc.y), (hero.x, hero.y))
                if path:
                    for i in range(len(path)):
                        if i >= npc.sp: break
                        if path[i] == (hero.x, hero.y): break
                        tx, ty = path[i]
                        occupied = any(c.x == tx and c.y == ty for c in self.combatants)
                        if occupied: break
                        npc.x, npc.y = tx, ty
                    self.replay_log.append(f"{npc.name} pursues {hero.name}.")
                    self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})
            else:
                npc.sp += 5
                self.replay_log.append(f"{npc.name} pauses to recover breath.")
                self.pending_updates.append({"type": "FCT", "text": "RESTING...", "pos": [npc.x, npc.y], "style": "miss"})

    def end_round(self):
        """Regenerate SP and pulse round counter."""
        self.round_count += 1
        self.reactions_used.clear() # Clear reactions for new round
        for c in self.combatants:
            if c.hp > 0:
                c.sp = min(c.max_sp, c.sp + 5)
        self.replay_log.append(f"--- Round {self.round_count} Begins ---")

    def attack_target(self, attacker, target):
        logs = []
        v_updates = []
        
        atk_stats = attacker.get_component(Stats)
        def_stats = target.get_component(Stats)
        
        # 0. Check Traits for Recoil/Bonus
        context = {"def_bonus": 0, "force_miss": False}
        r_logs, r_updates = self.handle_reactions(attacker, target, "BEFORE_ATTACK", context)
        logs.extend(r_logs)
        v_updates.extend(r_updates)

        sp_cost = 2
        if attacker.sp < sp_cost:
            logs.append(f"{attacker.name} is too tired to strike!")
            v_updates.append({"type": "FCT", "text": "TIRED", "pos": [attacker.x, attacker.y], "style": "dmg"})
            return logs, v_updates
        
        attacker.sp -= sp_cost
        atk_might = atk_stats.get("Might", 10) if atk_stats else 10
        def_reflex = (def_stats.get("Reflexes", 10) if def_stats else 10) + context["def_bonus"]
        
        if context["force_miss"]:
            atk_roll = 1
        else:
            atk_roll = random.randint(1, 20) + (atk_might // 2)
            
        def_roll = random.randint(1, 20) + (def_reflex // 2)
        margin = atk_roll - def_roll
        
        logs.append(f"{attacker.name} strikes {target.name}: {atk_roll} vs {def_roll} (Margin: {margin})")
        
        if margin >= 10: 
            dmg = 15
            target.take_damage(dmg)
            logs.append(f"CRITICAL! {target.name} takes {dmg} DMG.")
            v_updates.extend([
                {"type": "FCT", "text": f"-{dmg} HP!", "pos": [target.x, target.y], "style": "crit"},
                {"type": "SHAKE", "intensity": 5}
            ])
            # Post-Damage Reactions
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs)
            v_updates.extend(dr_updates)
        elif margin > 0: 
            dmg = 8
            target.take_damage(dmg)
            logs.append(f"HIT! {target.name} takes {dmg} DMG.")
            v_updates.append({"type": "FCT", "text": f"-{dmg}", "pos": [target.x, target.y], "style": "dmg"})
            # Post-Damage Reactions
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs)
            v_updates.extend(dr_updates)
        else:
            logs.append(f"{target.name} evades!")
            v_updates.append({"type": "FCT", "text": "MISS", "pos": [target.x, target.y], "style": "miss"})
            
        return logs, v_updates

    def move_char(self, char, tx, ty):
        if not (0 <= tx < self.cols and 0 <= ty < self.rows):
            return False, "Boundaries reached."
        if (tx, ty) in self.walls:
            return False, "Path blocked."
        
        base_cost = 1
        if self.terrain.get((tx, ty)) == "DIFFICULT":
            base_cost = 2
            
        moves = max(abs(char.x - tx), abs(char.y - ty))
        sp_needed = moves * base_cost
        
        if char.sp < sp_needed:
            return False, f"Not enough SP! ({sp_needed} required)"
            
        char.sp -= sp_needed
        char.x, char.y = tx, ty
        return True, f"Moved to {tx},{ty} (-{sp_needed} SP)."
