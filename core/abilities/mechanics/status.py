def handle_stun(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 1)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Stunned", duration)
        else:
            t.is_stunned = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Stunned for {duration} round(s)!")

def handle_paralyze(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 1)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Paralyzed", duration)
        else:
            t.is_paralyzed = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Paralyzed for {duration} round(s)!")

def handle_poison(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 3)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Poisoned", duration)
        else:
            t.is_poisoned = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Poisoned for {duration} round(s)!")

def handle_fear(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 1)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Frightened", duration)
        else:
            t.is_frightened = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Frightened for {duration} round(s)!")

def handle_charm(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 1)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Charmed", duration)
        else:
            t.is_charmed = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Charmed for {duration} round(s)!")

def handle_deafen(match, ctx):
    t = ctx.get("target")
    if t: 
        duration = ctx.get("effect_duration", 1)
        if hasattr(t, "apply_effect"):
            t.apply_effect("Deafened", duration)
        else:
            t.is_deafened = True
        if "log" in ctx: ctx["log"].append(f"{t.name} Deafened for {duration} round(s)!")

def handle_blindness(match, ctx):
    t = ctx.get("target")
    if t:
        duration = 1
        if hasattr(t, "apply_effect"):
            t.apply_effect("Blinded", duration)
        else:
            t.is_blinded = True
        if "log" in ctx: ctx["log"].append(f"{t.name} is Blinded!")

def handle_perm_blind(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"):
            t.apply_effect("Blinded", -1) # Permanent
        if "log" in ctx: ctx["log"].append(f"{t.name} is Permanently Blinded!")

def handle_dazzle(match, ctx):
    t = ctx.get("target")
    if t:
        # Dazzle might be a custom -1 to Hit effect or just description
        if "log" in ctx: ctx["log"].append(f"{t.name} is Dazzled (-1 to Hit)!")
        # Implementation depends on engine supporting 'dazzled' state

def handle_save_condition(match, ctx):
    """
    Pattern: save.*?or.*?(Prone|Frightened|Charmed|Blinded|Paralyzed|Poisoned|Stunned|Restrained|Deafened)
    """
    condition = match.group(1)
    target = ctx.get("target")
    attacker = ctx.get("attacker")
    
    # We need a save logic here. Assuming mechanics clears 'save_success' flag in context?
    # Or we roll it here.
    save_success = False
    if target and hasattr(target, "roll_save"):
        # Determine save type from context or default
        save_type = "Endurance" # Default
        if condition in ["Frightened", "Charmed"]: save_type = "Willpower"
        elif condition in ["Prone", "Blinded"]: save_type = "Reflexes"
        
        # DC?
        dc = 12 
        if attacker: dc = 10 + (getattr(attacker, "level", 1) // 2)
        
        save_val, nat = target.roll_save(save_type)
        if save_val >= dc:
            save_success = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Saved vs {condition} ({save_val} vs DC {dc})")
        else:
            if "log" in ctx: ctx["log"].append(f"{target.name} Failed Save vs {condition} ({save_val} vs DC {dc})")
            
    if not save_success and target:
        if hasattr(target, "apply_effect"):
            target.apply_effect(condition, 1)

def handle_inflict_disease(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "apply_effect"):
        t.apply_effect("Diseased", -1)
        if "log" in ctx: ctx["log"].append(f"{t.name} is Diseased!")

def handle_insanity(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "apply_effect"):
        t.apply_effect("Insane", -1)
        if "log" in ctx: ctx["log"].append(f"{t.name} mind shatters!")

def handle_hesitate(match, ctx):
    t = ctx.get("target")
    if t and hasattr(t, "apply_effect"):
        # Skip turn?
        if "log" in ctx: ctx["log"].append(f"{t.name} Hesitates (Skips Turn).")

def handle_enrage(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"): t.apply_effect("Rage", 3)
        if "log" in ctx: ctx["log"].append(f"{t.name} goes Berserk!")

def handle_dominate_charm(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"): t.apply_effect("Dominated", 3)
        if "log" in ctx: ctx["log"].append(f"{t.name} is Dominated by the attacker!")

def handle_silence(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"): t.apply_effect("Silenced", 3)
        if "log" in ctx: ctx["log"].append(f"{t.name} is Silenced!")

def handle_petrify(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"): t.apply_effect("Petrified", -1)
        if "log" in ctx: ctx["log"].append(f"{t.name} turns to Stone!")

def handle_sleep(match, ctx):
    t = ctx.get("target")
    if t:
        if hasattr(t, "apply_effect"): t.apply_effect("Asleep", 10)
        if "log" in ctx: ctx["log"].append(f"{t.name} falls Asleep!")
