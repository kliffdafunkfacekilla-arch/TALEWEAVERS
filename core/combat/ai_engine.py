
import random
import math

class AIDecisionEngine:
    """
    Handles tactical decision making for AI combatants.
    Enhanced with ranged attacks, skill/ability usage, and resource management.
    """
    def __init__(self):
        # Track which abilities we've already tried this combat to avoid spam
        self.tried_abilities = {}

    def evaluate_turn(self, combatant, engine):
        """
        Main entry point for AI thinking.
        Returns a list of log strings.
        """
        log = [f"[AI] {combatant.name} is thinking..."]
        
        # 1. Analyze Battlefield
        context = self.analyze_battlefield(combatant, engine)
        
        # 2. Determine Strategy (Behavior Template)
        template = combatant.data.get("AI", "Aggressive")
        
        # 3. Select Action
        action_log = self.select_action(combatant, context, template, engine)
        log.extend(action_log)
        
        return log

    def analyze_battlefield(self, me, engine):
        """
        Gathers context: visible enemies, allies, health states, clusters.
        """
        enemies = []
        allies = []
        
        my_team = getattr(me, "team", "Enemy") 
        
        for c in engine.combatants:
            if not c.is_alive(): continue
            if c == me: continue
            
            c_team = getattr(c, "team", "Player")
            dist = max(abs(me.x - c.x), abs(me.y - c.y))
            
            info = {"obj": c, "dist": dist, "hp_pct": c.hp / c.max_hp}
            
            if c_team == my_team:
                allies.append(info)
            else:
                enemies.append(info)
                
        # Find Clusters
        clusters = []
        for e in enemies:
            count = 0
            start_x, start_y = e["obj"].x, e["obj"].y
            for other in enemies:
                if max(abs(start_x - other["obj"].x), abs(start_y - other["obj"].y)) <= 2:
                    count += 1
            if count > 1:
                clusters.append({"center": e["obj"], "count": count})
        
        clusters.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "enemies": sorted(enemies, key=lambda x: x["dist"]),
            "allies": sorted(allies, key=lambda x: x["hp_pct"]),
            "clusters": clusters,
            "my_hp_pct": me.hp / me.max_hp
        }

    # ==================== WEAPON DETECTION ====================
    
    def _get_weapon_info(self, me):
        """
        Returns weapon info: (is_ranged, range_tiles, has_melee_backup)
        """
        if not me.inventory:
            return (False, 1, False)  # Unarmed = melee
            
        main_hand = me.inventory.equipped.get("Main Hand")
        off_hand = me.inventory.equipped.get("Off Hand")
        
        is_ranged = False
        range_tiles = 1
        has_melee_backup = False
        
        if main_hand:
            # Check for RANGE tag in weapon
            tags = getattr(main_hand, "tags", {})
            if "RANGE" in tags or hasattr(main_hand, "range_short"):
                is_ranged = True
                range_tiles = getattr(main_hand, "range_short", 6)
        
        if off_hand and not getattr(off_hand, "range_short", None):
            has_melee_backup = True
            
        return (is_ranged, range_tiles, has_melee_backup)

    # ==================== ABILITY USAGE ====================
    
    def _has_resources(self, me):
        return me.fp >= 2 or me.sp >= 2

    def _is_offensive_ability(self, ability_name, engine):
        """
        Check if ability is Offense type (worth using in combat).
        """
        try:
            from abilities import engine_hooks
            data = engine_hooks.get_ability_data(ability_name)
            if data:
                ability_type = data.get("Type", "").lower()
                return ability_type == "offense"
        except:
            pass
        return False  # Default: don't use if we can't verify

    def _try_use_ability(self, me, target, engine, log, template):
        """
        Attempts to use an OFFENSIVE ability from powers list.
        Only tries offensive abilities, skips utility/defense.
        Returns True if ability was SUCCESSFULLY used.
        """
        if template == "Opportunist":
            if me.hp / me.max_hp > 0.5:
                return False
        
        if not self._has_resources(me):
            return False
        
        # Try each power - but only OFFENSIVE ones
        for power in me.powers:
            # Skip non-offensive abilities
            if not self._is_offensive_ability(power, engine):
                continue
            
            # Check range
            dist = max(abs(me.x - target.x), abs(me.y - target.y))
            if dist > 6:
                continue
            
            try:
                result = engine.activate_ability(me, power, target)
                if result:
                    result_str = " ".join(str(r) for r in result)
                    
                    if "Not enough" in result_str:
                        continue
                    if "No effect resolved" in result_str:
                        continue
                    if "data not found" in result_str:
                        continue
                    
                    log.extend(result if isinstance(result, list) else [str(result)])
                    log.append(f"[AI] Used {power}!")
                    return True
            except Exception as e:
                print(f"AI ERROR: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        return False

    # ==================== MOVEMENT & KITING ====================
    
    def _move_away_from(self, me, target, engine, log):
        dx = me.x - target.x
        dy = me.y - target.y
        
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        new_x, new_y = me.x + step_x, me.y + step_y
        new_x = max(0, min(engine.cols - 1, new_x))
        new_y = max(0, min(engine.rows - 1, new_y))
        
        success, msg = engine.move_char(me, new_x, new_y)
        if success:
            log.append(f"[AI] Kiting: {msg}")
        return success

    # ==================== ATTACK ROUTINES ====================
    
    def _ranged_attack_routine(self, me, target, engine, log, max_range, has_melee):
        dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        if dist <= 1 and not has_melee:
            log.append(f"[AI] Target too close, kiting...")
            self._move_away_from(me, target, engine, log)
            dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        if dist <= 1 and has_melee:
            log.append(f"[AI] Switching to melee!")
            log.extend(engine.attack_target(me, target))
            return
        
        if dist <= max_range:
            log.append(f"[AI] Ranged attack from {dist * 5}ft!")
            log.extend(engine.attack_target(me, target))
        else:
            dx, dy = target.x - me.x, target.y - me.y
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            new_x, new_y = me.x + step_x, me.y + step_y
            success, msg = engine.move_char(me, new_x, new_y)
            log.append(f"[AI] Closing range: {msg}")
            
            dist = max(abs(me.x - target.x), abs(me.y - target.y))
            if dist <= max_range:
                log.extend(engine.attack_target(me, target))

    def _melee_attack_routine(self, me, target, engine, log):
        dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        while dist > 1 and me.movement_remaining >= 5:
            dx, dy = target.x - me.x, target.y - me.y
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            new_x, new_y = me.x + step_x, me.y + step_y
            success, msg = engine.move_char(me, new_x, new_y)
            if not success:
                break
            log.append(f"[AI] Move: {msg}")
            dist = max(abs(me.x - target.x), abs(me.y - target.y))

        if dist <= 1:
            log.extend(engine.attack_target(me, target))
        else:
            log.append(f"[AI] Closing distance to {target.name}")

    def _basic_attack_routine(self, me, target, engine, log):
        is_ranged, max_range, has_melee = self._get_weapon_info(me)
        
        if is_ranged:
            self._ranged_attack_routine(me, target, engine, log, max_range, has_melee)
        else:
            self._melee_attack_routine(me, target, engine, log)

    # ==================== ACTION SELECTION ====================

    def select_action(self, me, ctx, template, engine):
        """
        Executes the best action based on template priorities.
        Now: Try ONE offensive ability, then ALWAYS do basic attack.
        """
        log = []
        
        if not ctx["enemies"]:
            log.append("[AI] No targets visible.")
            return log
            
        target = ctx["enemies"][0]["obj"]
        
        # Step 1: Try ONE offensive ability (but don't return - keep going)
        if template != "Opportunist":
            self._try_use_ability(me, target, engine, log, template)
            # Continue to basic attack regardless of ability success
        
        # Step 2: ALWAYS do basic attack routine as well
        self._basic_attack_routine(me, target, engine, log)
            
        return log
