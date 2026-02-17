def handle_push(match, ctx):
    dist = int(match.group(1))
    target = ctx.get("target")
    if target: 
        # In a real grid, modify (x,y). For simple engine:
        if "log" in ctx: ctx["log"].append(f"{target.name} is Pushed {dist}ft!")

def handle_save_push(match, ctx):
    dist = int(match.group(1))
    target = ctx.get("target")
    attacker = ctx.get("attacker")
    success = False
    
    if target and hasattr(target, "roll_save"):
        dc = 12
        val, nat = target.roll_save("Might") # Strength save vs push usually
        if val >= dc: success = True
    
    if not success and target:
        if "log" in ctx: ctx["log"].append(f"{target.name} Failed Save and is Pushed {dist}ft!")
    else:
        if "log" in ctx: ctx["log"].append(f"{target.name} Resisted Push.")

def handle_teleport(match, ctx):
    dist = int(match.group(1))
    user = ctx.get("attacker")
    if user:
        if "log" in ctx: ctx["log"].append(f"{user.name} Teleports {dist}ft!")

def handle_fly_speed(match, ctx):
    user = ctx.get("attacker") or ctx.get("target")
    if user:
         # Simplified speed buff
         if "log" in ctx: ctx["log"].append(f"{user.name} gains Fly Speed.")

def handle_swim_speed(match, ctx):
    user = ctx.get("attacker") or ctx.get("target")
    if user:
         if "log" in ctx: ctx["log"].append(f"{user.name} gains Swim Speed.")

def handle_climb_speed(match, ctx):
    user = ctx.get("attacker") or ctx.get("target")
    if user:
         if "log" in ctx: ctx["log"].append(f"{user.name} gains Climb Speed.")
         
def handle_burrow_speed(match, ctx):
    user = ctx.get("attacker") or ctx.get("target")
    if user:
         if "log" in ctx: ctx["log"].append(f"{user.name} gains Burrow Speed.")

def handle_charge(match, ctx):
    # Line Charge
    attacker = ctx.get("attacker")
    if attacker:
        if "log" in ctx: ctx["log"].append(f"{attacker.name} Charges in a line!")

def handle_dash(match, ctx):
    attacker = ctx.get("attacker")
    if attacker:
        if "log" in ctx: ctx["log"].append(f"{attacker.name} Dashes (Extra Move).")

def handle_phase_move(match, ctx):
    attacker = ctx.get("attacker")
    if attacker:
        if "log" in ctx: ctx["log"].append(f"{attacker.name} moves through enemies (Phasing).")

def handle_phase_walk(match, ctx):
    attacker = ctx.get("attacker")
    if attacker:
        if "log" in ctx: ctx["log"].append(f"{attacker.name} walks through walls!")

def handle_escape_grapple(match, ctx):
    t = ctx.get("target") or ctx.get("attacker") # Self escape
    if t and hasattr(t, "remove_effect"):
        t.remove_effect("Grappled")
        t.remove_effect("Restrained")
        if "log" in ctx: ctx["log"].append(f"{t.name} Escapes Grapple!")

def handle_halt_movement(match, ctx):
    t = ctx.get("target")
    if t:
        if "log" in ctx: ctx["log"].append(f"{t.name} cannot move (Speed 0).")

def handle_black_hole(match, ctx):
    if "log" in ctx: ctx["log"].append("Black Hole pulls targets (AOE Pull).")

def handle_squeeze(match, ctx):
    if "log" in ctx: ctx["log"].append("Entity squeezes through small space.")

def handle_wall_walk(match, ctx):
    if "log" in ctx: ctx["log"].append("Entity walks on walls.")

def handle_stand_up(match, ctx):
    t = ctx.get("target") or ctx.get("attacker")
    if t:
        if hasattr(t, "is_prone"): t.is_prone = False
        if hasattr(t, "remove_effect"): t.remove_effect("Prone")
        if "log" in ctx: ctx["log"].append(f"{t.name} Stands Up.")

def handle_pull(match, ctx):
    dist_str = match.group(1)
    dist = int(dist_str) if dist_str else 5 # Default 5ft
    target = ctx.get("target")
    if target: 
        if "log" in ctx: ctx["log"].append(f"{target.name} is Pulled {dist}ft closer!")

def handle_jump_boost(match, ctx):
    user = ctx.get("attacker")
    if user:
        if "log" in ctx: ctx["log"].append(f"{user.name} boosts Jump height/distance.")

def handle_levitate(match, ctx):
    target = ctx.get("target") or ctx.get("attacker")
    if target:
        if "log" in ctx: ctx["log"].append(f"{target.name} Levitates (Floats).")

def handle_reverse_gravity(match, ctx):
    if "log" in ctx: ctx["log"].append("Gravity Reversed! (Ceiling is floor).")

def handle_launch(match, ctx):
    target = ctx.get("target")
    if target:
        if "log" in ctx: ctx["log"].append(f"{target.name} Launched a long distance!")
