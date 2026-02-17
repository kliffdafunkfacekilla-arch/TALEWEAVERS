import random

def handle_heal(match, ctx):
    """
    Pattern: Heal (\d+)d?(\d+)? ?(HP)?
    """
    if not match: return
    amt_str = match.group(1) or "1"
    die_str = match.group(2)
    
    target = ctx.get("target") or ctx.get("attacker") 
    # Logic: If self-cast, target is usually attacker. If applied to ally, target is ally.
    # We rely on engine context to provide correct 'target'.
    
    if not target: return

    heal = 0
    if die_str:
        num = int(amt_str)
        sides = int(die_str)
        heal = sum(random.randint(1, sides) for _ in range(num))
    else:
        heal = int(amt_str) if amt_str else 0
        
    old_hp = target.hp
    target.hp = min(target.hp + heal, target.max_hp)
    actual_heal = target.hp - old_hp
    
    if "log" in ctx: ctx["log"].append(f"{target.name} Healed {actual_heal} HP!")

def handle_temp_hp(match, ctx):
    user = ctx.get("attacker") or ctx.get("target")
    if user:
         # Simplified for now. Need TempHP stat in combatant.
         if hasattr(user, "temp_hp"):
             # Add amount? Pattern matches mostly just "Temp HP".
             # Assuming arbitrary amount or flat 5 for now if not specified.
             user.temp_hp += 5
             if "log" in ctx: ctx["log"].append(f"{user.name} gained 5 Temporary HP.")

def handle_temp_hp_buff(match, ctx):
    """Gain Temporary HP logic"""
    handle_temp_hp(match, ctx)

def handle_restore_resource(match, ctx):
    """Regain (\d+) (Stamina|Focus|FP|SP)"""
    amt = int(match.group(1))
    res = match.group(2)
    target = ctx.get("target") or ctx.get("attacker")
    if target:
        if res in ["Stamina", "SP"]:
            target.sp = min(target.sp + amt, target.max_sp)
        elif res in ["Focus", "FP"]:
            target.fp = min(target.fp + amt, target.max_fp)
        elif res == "CMP":
             target.cmp = min(target.cmp + amt, target.max_cmp)
        if "log" in ctx: ctx["log"].append(f"{target.name} regained {amt} {res}.")

def handle_regeneration(match, ctx):
    t = ctx.get("target") or ctx.get("attacker")
    if t and hasattr(t, "apply_effect"):
        t.apply_effect("Regeneration", 3)
        if "log" in ctx: ctx["log"].append(f"{t.name} gains Regeneration.")

def handle_minor_heal(match, ctx):
    # Fixed small heal
    t = ctx.get("target") or ctx.get("attacker")
    if t:
        t.hp = min(t.hp + 5, t.max_hp)
        if "log" in ctx: ctx["log"].append(f"{t.name} heals minor wounds (5 HP).")

def handle_full_heal(match, ctx):
    t = ctx.get("target")
    if t:
        t.hp = t.max_hp
        if "log" in ctx: ctx["log"].append(f"{t.name} is Fully Healed!")

def handle_stop_bleed(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "remove_effect"):
        t.remove_effect("Bleeding")
        if "log" in ctx: ctx["log"].append(f"{t.name} stops bleeding.")

def handle_cure_disease(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "remove_effect"):
        t.remove_effect("Diseased")
        if "log" in ctx: ctx["log"].append(f"{t.name} is Cured of Disease.")

def handle_cure_poison(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "remove_effect"):
        t.remove_effect("Poisoned")
        if "log" in ctx: ctx["log"].append(f"{t.name} is Cured of Poison.")

def handle_lifesteal(match, ctx):
    """Lifesteal / Heal for Dmg"""
    attacker = ctx.get("attacker")
    damage_dealt = ctx.get("damage_dealt", 0)
    if attacker and damage_dealt > 0:
        heal = damage_dealt // 2
        attacker.hp = min(attacker.hp + heal, attacker.max_hp)
        if "log" in ctx: ctx["log"].append(f"{attacker.name} drains {heal} HP from the attack!")

def handle_consume_ally(match, ctx):
    attacker = ctx.get("attacker")
    target = ctx.get("target")
    # This implies targeting an ally to eat them.
    if attacker and target:
         heal = target.hp
         target.hp = 0
         attacker.hp = min(attacker.hp + heal, attacker.max_hp)
         if "log" in ctx: ctx["log"].append(f"{attacker.name} consumes {target.name} to heal {heal} HP!")

def handle_resurrect(match, ctx):
    t = ctx.get("target")
    if t and t.hp <= 0:
        t.hp = 1
        t.is_dead = False # Assuming dead flag exists
        if "log" in ctx: ctx["log"].append(f"{t.name} comes back to life!")

def handle_auto_life(match, ctx):
    t = ctx.get("target") or ctx.get("attacker")
    if t and hasattr(t, "apply_effect"):
        t.apply_effect("Auto-Life", -1)
        if "log" in ctx: ctx["log"].append(f"{t.name} has Auto-Life.")

def handle_life_bond(match, ctx):
    if "log" in ctx: ctx["log"].append("Life Bond (Shared HP) active.")
