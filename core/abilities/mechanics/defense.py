def handle_resistance(match, ctx):
    """Resistance to (\w+)"""
    res_type = match.group(1)
    target = ctx.get("target") or ctx.get("attacker") # Self buff or target buff
    if target:
         if "log" in ctx: ctx["log"].append(f"{target.name} gains Resistance to {res_type}.")
         # In combat context, this might need to modify 'damage_taken' if triggered during damage calc
         if "damage_type" in ctx and ctx.get("damage_type") == res_type:
             if "damage_taken" in ctx: 
                 ctx["damage_taken"] //= 2
                 if "log" in ctx: ctx["log"].append("Damage Halved (Resistance).")

def handle_immunity(match, ctx):
    """Immune to (\w+)"""
    res_type = match.group(1)
    target = ctx.get("target") or ctx.get("attacker")
    if target:
         if "log" in ctx: ctx["log"].append(f"{target.name} is Immune to {res_type}.")
         if "damage_type" in ctx and ctx.get("damage_type") == res_type:
             if "damage_taken" in ctx: 
                 ctx["damage_taken"] = 0
                 if "log" in ctx: ctx["log"].append("Damage Negated (Immunity).")

def handle_halve_damage(match, ctx):
    if "damage_taken" in ctx:
        ctx["damage_taken"] //= 2
        if "log" in ctx: ctx["log"].append("Damage Halved.")

def handle_ac_buff(match, ctx):
    """+(\d+) (AC|Armor Class)"""
    amt = int(match.group(1))
    target = ctx.get("target") or ctx.get("attacker") # Usually self
    if target:
        # If this is a passive setup, we might modify stats.
        # If active context, just log it or apply temp effect?
        # Assuming temp effect for now or context modifier
        if "defense_mod" in ctx:
             ctx["defense_mod"] += amt
        if "log" in ctx: ctx["log"].append(f"AC increased by {amt}.")

def handle_natural_armor(match, ctx):
    if "log" in ctx: ctx["log"].append("Natural Armor Applied (See Sheet).")

def handle_natural_armor_formula(match, ctx):
    # 13 + Dex
    if "log" in ctx: ctx["log"].append("Natural Armor Formula Set.")

def handle_crit_immunity(match, ctx):
    if "crit_immune" in ctx:
        ctx["crit_immune"] = True # Flag for engine
    if "log" in ctx: ctx["log"].append("Immune to Critical Hits.")

def handle_shield_ally(match, ctx):
    if "log" in ctx: ctx["log"].append("Shielding Ally (Cover).")

def handle_reaction_ac(match, ctx):
    if "defense_mod" in ctx:
        ctx["defense_mod"] += 2 # Standard reaction bonus?
    if "log" in ctx: ctx["log"].append("Reaction Dodge (+2 AC).")

def handle_dense_skin(match, ctx):
    handle_resistance(type("Match", (), {"group": lambda s, n: "Physical"})(), ctx)

def handle_reflect_ray(match, ctx):
    if "log" in ctx: ctx["log"].append("Ray spell reflected!")
    
def handle_absorb_damage(match, ctx):
    # Take damage for ally
    if "log" in ctx: ctx["log"].append("Absorbing damage for ally.")

def handle_absorb_all(match, ctx):
    if "log" in ctx: ctx["log"].append("Absorbing ALL damage.")
    if "damage_taken" in ctx: ctx["damage_taken"] = 0

def handle_absorb_shock(match, ctx):
    # Heal from lightning?
    if "damage_type" in ctx and ctx["damage_type"] == "Lightning":
         if "damage_taken" in ctx: ctx["damage_taken"] = 0
         if "log" in ctx: ctx["log"].append("Shock Absorbed!")

def handle_immovable(match, ctx):
    if "log" in ctx: ctx["log"].append("Entity is Immovable.")

def handle_invulnerability(match, ctx):
    if "log" in ctx: ctx["log"].append("Entity is Invulnerable!")
    if "damage_taken" in ctx: ctx["damage_taken"] = 0

def handle_withdraw(match, ctx):
    # Turtle shell
    handle_ac_buff(type("Match", (), {"group": lambda s, n: "5"})(), ctx)
    if "log" in ctx: ctx["log"].append("Withdrawn into Shell (+5 AC).")

def handle_calculate_defense(match, ctx):
    if "log" in ctx: ctx["log"].append("Calculating Defense Pattern.")

def handle_parry(match, ctx):
    """Parry: Reduce incoming melee damage"""
    if "damage_taken" in ctx and "damage_type" in ctx and ctx["damage_type"] == "Physical":
        reduce = 3 # Basic parry value, could scale
        ctx["damage_taken"] = max(0, ctx["damage_taken"] - reduce)
        if "log" in ctx: ctx["log"].append(f"Parried! Reduced damage by {reduce}.")

def handle_deflect(match, ctx):
    """Deflect: Redirect attack to adjacent (Narrative/Log only for now)"""
    if "log" in ctx: ctx["log"].append("Deflected attack to side!")

def handle_flow(match, ctx):
    """Flow: Move 5ft when hit (Reaction)"""
    if "log" in ctx: ctx["log"].append("Flows with the hit (5ft shift).")

def handle_amorphous(match, ctx):
    """Liquid form"""
    if "crit_immune" in ctx: ctx["crit_immune"] = True
    if "log" in ctx: ctx["log"].append("Amorphous (Immune to Crits/Grapple).")

def handle_intangible(match, ctx):
    """Permanent Phasing"""
    if "log" in ctx: ctx["log"].append("Intangible (Phasing).")

def handle_catch(match, ctx):
    """Catch: Snatch weapon/item thrown at you."""
    if "damage_taken" in ctx and "damage_type" in ctx and ctx["damage_type"] == "Physical":
        ctx["damage_taken"] = 0
        if "log" in ctx: ctx["log"].append("Caught the projectile! (0 Damage)")

def handle_brace(match, ctx):
    """Brace: Ignore Knockback/Prone"""
    if "log" in ctx: ctx["log"].append("Braced! (Immune to Knockback/Prone)")

def handle_orbit(match, ctx):
    """Orbit: Shield of debris"""
    # Mechanically could be temp HP or AC
    handle_ac_buff(type("Match", (), {"group": lambda s, n: "2"})(), ctx)
    if "log" in ctx: ctx["log"].append("Debris Orbit (+2 AC).")

def handle_event_horizon(match, ctx):
    """Event Horizon: Absorb magical projectiles"""
    # Simplistic implementation: Negate damage if magical/projectile context?
    if "log" in ctx: ctx["log"].append("Event Horizon Active (Absorbs Magic).")

def handle_reflect_damage(match, ctx):
    """Reflect incoming damage back to attacker"""
    if "log" in ctx: ctx["log"].append("Reflecting Damage!")
    if "damage_taken" in ctx:
        # Simplistic reflection logging
        amt = ctx["damage_taken"]
        ctx["damage_taken"] = 0
        if "attacker" in ctx and ctx["attacker"]:
             # If engine allows, deal damage back. For now log.
             ctx["log"].append(f"Reflected {amt} damage back to attacker.")
