import random
from typing import List, Dict, Any, Tuple
from core.ecs import Entity, Stats, Position, Vitals

class CombatEngine:
    def __init__(self, cols: int, rows: int, combatants: List[Entity] = None):
        self.cols = cols
        self.rows = rows
        self.combatants = combatants if combatants is not None else []
        self.terrain = {}
        self.walls = set()
        self.grid_cells = None
        self.round_count = 1
        self.reactions_used = set()
        self.replay_log = []
        self.pending_updates = []

    def set_map(self, grid_cells: List[List[int]], walls: List[Tuple[int, int]]):
        self.grid_cells = grid_cells
        self.walls = set(walls)

    def find_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* implementation placeholder."""
        path = []
        curr_x, curr_y = start
        tx, ty = end
        
        while (curr_x != tx or curr_y != ty) and len(path) < 20:
            if curr_x < tx: curr_x += 1
            elif curr_x > tx: curr_x -= 1
            elif curr_y < ty: curr_y += 1
            elif curr_y > ty: curr_y -= 1
            
            if (curr_x, curr_y) in self.walls: break
            path.append((curr_x, curr_y))
            
        return path

    def has_los(self, x1, y1, x2, y2):
        """Line of Sight check."""
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0: return True
        
        for i in range(1, steps):
            tx = int(x1 + (dx * i / steps))
            ty = int(y1 + (dy * i / steps))
            if (tx, ty) in self.walls:
                return False
        return True

    def process_intent(self, player: Entity, intent: Dict[str, Any]):
        action = intent.get("action")
        target_id = intent.get("target")
        params = intent.get("params", {})
        skill_used = intent.get("skill_used")

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
                    atk_logs, atk_updates = self.attack_target(player, target, skill_used=skill_used)
                    log.extend(atk_logs)
                    updates.extend(atk_updates)
                    updates.append({"type": "UPDATE_HP", "id": target.id, "hp": target.hp})
                    updates.append({"type": "UPDATE_HP", "id": player.id, "hp": player.hp})
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
        if (tx, ty) not in self.walls:
            return False, "There is nothing robust to smash here.", []
            
        dist = max(abs(char.x - tx), abs(char.y - ty))
        if dist > 1: return False, "Target too far to smash.", []
            
        sp_cost = 3
        if char.sp < sp_cost:
            return False, f"Too exhausted to smash! (Need {sp_cost} SP)", []
            
        stats = char.get_component(Stats)
        might = stats.get("Might", 10) if stats else 10
        check = random.randint(1, 20) + (might // 2)
        char.sp -= sp_cost
        
        if check >= 15:
            self.walls.remove((tx, ty))
            if self.grid_cells: self.grid_cells[ty][tx] = 129
            return True, f"{char.name} SMASHES the obstacle!", [{"type": "SHAKE", "intensity": 8}, {"type": "FCT", "text": "SMASH!", "pos": [tx, ty], "style": "crit"}]
        else:
            return False, f"{char.name} fails to break the obstacle.", [{"type": "FCT", "text": "CLANG", "pos": [tx, ty], "style": "dmg"}]

    def run_ai_turn(self):
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
                        if not any(c.x == tx and c.y == ty for c in self.combatants):
                            npc.x, npc.y = tx, ty
                    self.pending_updates.append({"type": "MOVE_TOKEN", "id": npc.id, "pos": [npc.x, npc.y]})

    def end_round(self):
        self.round_count += 1
        self.reactions_used.clear()
        for c in self.combatants:
            if c.hp > 0: c.sp = min(c.max_sp, c.sp + 5)

    def attack_target(self, attacker, target, skill_used=None):
        logs = []
        v_updates = []
        atk_stats = attacker.get_component(Stats)
        def_stats = target.get_component(Stats)
        context = {"def_bonus": 0, "force_miss": False, "skill_bonus": 0}
        
        if skill_used:
            logs.append(f"[SKILL] {attacker.name} uses {skill_used}!")
            v_updates.append({"type": "FCT", "text": skill_used.upper(), "pos": [attacker.x, attacker.y], "style": "react"})
            context["skill_bonus"] = 2

        r_logs, r_updates = self.handle_reactions(attacker, target, "BEFORE_ATTACK", context)
        logs.extend(r_logs)
        v_updates.extend(r_updates)

        sp_cost = 2 if not skill_used else 4
        if attacker.sp < sp_cost:
            logs.append(f"{attacker.name} is too tired!")
            v_updates.append({"type": "FCT", "text": "TIRED", "pos": [attacker.x, attacker.y], "style": "dmg"})
            return logs, v_updates
        
        attacker.sp -= sp_cost
        atk_might = atk_stats.get("Might", 10) if atk_stats else 10
        def_reflex = (def_stats.get("Reflexes", 10) if def_stats else 10) + context["def_bonus"]
        
        atk_roll = random.randint(1, 20) + (atk_might // 2) + context["skill_bonus"] if not context["force_miss"] else 1
        def_roll = random.randint(1, 20) + (def_reflex // 2)
        margin = atk_roll - def_roll
        
        if margin >= 10: 
            dmg = 15 if not skill_used else 25
            target.take_damage(dmg)
            logs.append(f"CRITICAL! {target.name} takes {dmg} DMG.")
            v_updates.extend([{"type": "FCT", "text": f"-{dmg} HP!", "pos": [target.x, target.y], "style": "crit"},{"type": "SHAKE", "intensity": 5}])
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs); v_updates.extend(dr_updates)
        elif margin > 0: 
            dmg = 8 if not skill_used else 14
            target.take_damage(dmg)
            logs.append(f"HIT! {target.name} takes {dmg} DMG.")
            v_updates.append({"type": "FCT", "text": f"-{dmg}", "pos": [target.x, target.y], "style": "dmg"})
            dr_logs, dr_updates = self.handle_reactions(attacker, target, "POST_DAMAGE", {})
            logs.extend(dr_logs); v_updates.extend(dr_updates)
        else:
            logs.append(f"{target.name} evades!")
            v_updates.append({"type": "FCT", "text": "MISS", "pos": [target.x, target.y], "style": "miss"})
            
        return logs, v_updates

    def move_char(self, char, tx, ty):
        if not (0 <= tx < self.cols and 0 <= ty < self.rows): return False, "Boundaries reached."
        if (tx, ty) in self.walls: return False, "Path blocked."
        sp_needed = max(abs(char.x - tx), abs(char.y - ty)) * (2 if self.terrain.get((tx, ty)) == "DIFFICULT" else 1)
        if char.sp < sp_needed: return False, f"Not enough SP! ({sp_needed} required)"
        char.sp -= sp_needed
        char.x, char.y = tx, ty
        return True, f"Moved to {tx},{ty}."
