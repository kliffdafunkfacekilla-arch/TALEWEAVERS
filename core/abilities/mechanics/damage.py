import random

def handle_deal_damage(match, ctx):
    """
    Pattern: Deal (\d+)?d?(\d+)? ?(\w+) Damage
    Ex: "Deal 1d6 Fire Damage", "Deal 5 Damage"
    """
    amt_str_1 = match.group(1) # Num dice
    die_str = match.group(2)   # Die size
    dmg_type = match.group(3) or "Physical"
    
    target = ctx.get("target")
    if not target: return

    damage = 0
    if die_str:
        num = int(amt_str_1) if amt_str_1 else 1
        sides = int(die_str)
        damage = sum(random.randint(1, sides) for _ in range(num))
    else:
        damage = int(amt_str_1) if amt_str_1 else 0
        
    if "log" in ctx: 
        ctx["log"].append(f"Effect deals {damage} {dmg_type} damage!")
    
    if hasattr(target, "take_damage"):
        killed = target.take_damage(damage)
        if killed and "log" in ctx:
            ctx["log"].append(f"{target.name} is Slain!")

def handle_simple_damage(match, ctx):
    """
    Pattern: (\w+) Damage
    Ex: "Fire Damage"
    """
    dmg_type = match.group(1)
    # Usually implies adding a damage tag to an attack context
    if "damage_type" in ctx:
        ctx["damage_type"] = dmg_type
        if "log" in ctx: ctx["log"].append(f"Damage type changed to {dmg_type}")

def handle_magic_missile(match, ctx):
    """Auto-Hit / Magic Missile logic"""
    # Context usually implies an attack roll is being bypassed
    if "attack_roll" in ctx:
        ctx["attack_roll"] = 999 # Auto hit
        ctx["is_auto_hit"] = True
        if "log" in ctx: ctx["log"].append("Magic Missile! Auto-Hit!")

def handle_auto_hit(match, ctx):
    """Auto-Hit logic"""
    if "attack_roll" in ctx:
        ctx["attack_roll"] = 999 # Ensure hit
        ctx["is_auto_hit"] = True
        if "log" in ctx: ctx["log"].append("Attack Automatically Hits!")

def handle_auto_damage(match, ctx):
    """
    Pattern: Auto-Damage|No Roll
    """
    # Just a narrative flag or ensures damage step happens
    # Logic usually handled in handle_deal_damage if amount provided,
    # or this sets a flag for the engine.
    if "log" in ctx: ctx["log"].append("Damage is automatic (No roll required).")

def handle_fire_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 6) # Default small burn
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"Burning! Takes {dmg} Fire damage.")

def handle_cold_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 6)
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"Freezing! Takes {dmg} Cold damage.")

def handle_lightning_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 6)
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"Shocked! Takes {dmg} Lightning damage.")
        
def handle_acid_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 4)
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"Melting! Takes {dmg} Acid damage.")

def handle_force_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 4)
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"Force Burst! Takes {dmg} Force damage.")

def handle_sonic_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(1, 4)
        target.take_damage(dmg)
        # Sonic bypasses armor often
        if "log" in ctx: ctx["log"].append(f"Shatter! Takes {dmg} Sonic damage.")

def handle_nuclear_damage(match, ctx):
    target = ctx.get("target")
    if target and hasattr(target, "take_damage"):
        dmg = random.randint(10, 40) # 4d10
        target.take_damage(dmg)
        if "log" in ctx: ctx["log"].append(f"NUCLEAR FISSION! Takes {dmg} Radiant/Force damage.")

def handle_dot(match, ctx):
    """Damage over Time / Bleed"""
    target = ctx.get("target")
    if target:
        if hasattr(target, "apply_effect"):
             target.apply_effect("Bleeding", 3)
        if "log" in ctx: ctx["log"].append(f"{target.name} begins to Bleed.")

def handle_massive_dot(match, ctx):
    target = ctx.get("target")
    if target:
        if hasattr(target, "apply_effect"):
             target.apply_effect("Rot", 3)
        if "log" in ctx: ctx["log"].append(f"{target.name} is rotting away (Massive DoT).")

def handle_split_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Damage split among targets (Engine Implementation Required).")
    
def handle_reflect_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Reflect Damage active.")

def handle_lifesteal(match, ctx):
    """Lifesteal / Heal for Dmg"""
    attacker = ctx.get("attacker")
    damage_dealt = ctx.get("damage_dealt", 0)
    if attacker and damage_dealt > 0:
        heal = damage_dealt // 2
        attacker.hp = min(attacker.hp + heal, attacker.max_hp)
        if "log" in ctx: ctx["log"].append(f"{attacker.name} drains {heal} HP from the attack!")
