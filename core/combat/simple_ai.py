from combat.combat_engine import CombatEngine
from combat.combatant import Combatant
import random

class SimpleAI:
    """
    Standard driver for BRQSE combat simulations.
    Adapted for V4.0 Physics (Clash resolution and Channeling).
    """
    
    @staticmethod
    def execute_turn(me: Combatant, engine: CombatEngine):
        """
        Dispatches AI logic based on archetype. 
        Handles high-priority states like Clashes first.
        """
        # 1. Resolve pending Clashes
        if engine.clash_active:
            # Simple AI choice: Press if Might-based, else Disengage
            choice = "Press" if me.get_stat("Might") > 12 else "Disengage"
            engine.resolve_clash(choice)
            return

        # 2. Archetype Logic
        archetype = getattr(me, "ai_archetype", "Berserker")
        
        if archetype == "Sniper":
            SimpleAI._ai_ranged_sniper(me, engine)
        elif archetype == "Soldier":
            SimpleAI._ai_tactical_soldier(me, engine)
        elif archetype == "Social":
            SimpleAI._ai_social_manipulator(me, engine)
        else: # Default Berserker
            SimpleAI._ai_melee_berserker(me, engine)

    @staticmethod
    def _get_targets(me: Combatant, engine: CombatEngine):
        """Returns sorted list of (dist, combatant) enemies."""
        targets = []
        for c in engine.combatants:
            if c.is_alive and c.team != me.team:
                dist = max(abs(me.x - c.x), abs(me.y - c.y))
                targets.append((dist, c))
        targets.sort(key=lambda x: x[0])
        return targets

    @staticmethod
    def _ai_melee_berserker(me: Combatant, engine: CombatEngine):
        """Strategy: Aggressive Rush + Rare Chaos Channeling."""
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        
        dist, target = targets[0]
        
        # 5% Chance to Channel Chaos if in range (within 6 tiles)
        if dist <= 6 and random.random() < 0.05:
            engine.channel_chaos(me, target)
            return

        # MOVE
        if dist > 1:
            SimpleAI._move_towards(me, target, engine, 1)
            dist = max(abs(me.x - target.x), abs(me.y - target.y))
            
        # ATTACK
        if dist <= 1:
            engine.execute_attack(me, target, "Might")

    @staticmethod
    def _ai_ranged_sniper(me: Combatant, engine: CombatEngine):
        """Strategy: Kite. Maintain distance 4-8."""
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        
        dist, target = targets[0]
        min_range = 3
        max_range = 8
        
        # MOVE
        if dist < min_range:
            SimpleAI._move_away(me, target, engine)
        elif dist > max_range:
            SimpleAI._move_towards(me, target, engine, max_range)
            
        # ATTACK
        dist = max(abs(me.x - target.x), abs(me.y - target.y))
        if dist <= max_range + 2:
            engine.execute_attack(me, target, "Reflexes")

    @staticmethod
    def _ai_tactical_soldier(me: Combatant, engine: CombatEngine):
        """Strategy: Tactical. Covers and Kiting."""
        SimpleAI._ai_ranged_sniper(me, engine)

    @staticmethod
    def _move_towards(me, target, engine, desired_range):
        candidates = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(candidates)
        current_dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        for dx, dy in candidates:
            nx, ny = me.x + dx, me.y + dy
            new_dist = max(abs(nx - target.x), abs(ny - target.y))
            if new_dist < current_dist:
                if engine.move_entity(me, nx, ny):
                    return

    @staticmethod
    def _move_away(me, target, engine):
        candidates = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(candidates)
        current_dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        for dx, dy in candidates:
            nx, ny = me.x + dx, me.y + dy
            new_dist = max(abs(nx - target.x), abs(ny - target.y))
            if new_dist > current_dist:
                if engine.move_entity(me, nx, ny):
                    return

    @staticmethod
    def _ai_social_manipulator(me: Combatant, engine: CombatEngine):
        """Social logic (Simplified for simulation)."""
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        SimpleAI._ai_melee_berserker(me, engine)
