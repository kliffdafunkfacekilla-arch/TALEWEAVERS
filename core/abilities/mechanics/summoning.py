def handle_summon(match, ctx):
    if "log" in ctx: ctx["log"].append("Summoning Ally.")

def handle_create_terrain(match, ctx):
    type_ = match.group(1).lower()
    if "log" in ctx: ctx["log"].append(f"Creating Terrain: {type_}.")
    
    x, y = None, None
    if ctx.get("target_pos"):
        x, y = ctx["target_pos"]
        
    if x is not None and y is not None:
        if "engine" in ctx:
            ctx["engine"].pending_world_updates.append({
                "type": "terrain",
                "subtype": "wall" if "wall" in type_ else "hazard",
                "x": x,
                "y": y
            })

def handle_create_hazard(match, ctx):
    type_ = match.group(1)
    ele = (match.group(2) or "Generic").lower()
    if "log" in ctx: ctx["log"].append(f"Creating Hazard: {type_} ({ele}).")
    
    x, y = None, None
    if ctx.get("target_pos"):
        x, y = ctx["target_pos"]
    elif ctx.get("target"):
        x, y = ctx["target"].x, ctx["target"].y
        
    if x is not None and y is not None:
        if "engine" in ctx:
            ctx["engine"].pending_world_updates.append({
                "type": "terrain",
                "subtype": ele if ele in ["fire", "ice", "acid"] else "hazard",
                "x": x,
                "y": y
            })
            if "log" in ctx: ctx["log"].append(f"{ele.capitalize()} hazard materialized at {x},{y}!")

def handle_create_wall(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Wall.")
    
    # Needs target position.
    # Check ctx for target_pos (x, y) or derive from target entity
    x, y = None, None
    if ctx.get("target_pos"):
        x, y = ctx["target_pos"]
    elif ctx.get("target"):
        x, y = ctx["target"].x, ctx["target"].y
        
    if x is not None and y is not None:
        if "engine" in ctx:
            ctx["engine"].pending_world_updates.append({
                "type": "terrain",
                "subtype": "wall",
                "x": x,
                "y": y
            })
            if "log" in ctx: ctx["log"].append(f"Wall materialized at {x},{y}!")

def handle_create_construct(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Construct Automaton.")

def handle_animate_plant(match, ctx):
    if "log" in ctx: ctx["log"].append("Animating Plant.")

def handle_clone(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Clone.")

def handle_swarm_form(match, ctx):
    if "log" in ctx: ctx["log"].append("Transforming into Swarm.")

def handle_create_land(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating New Land.")

def handle_entomb(match, ctx):
    if "log" in ctx: ctx["log"].append("Entombing Target.")

def handle_fortress(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Fortress.")

def handle_web_shot(match, ctx):
    if "log" in ctx: ctx["log"].append("Shooting Web (Create Hazard).")

def handle_spore_cloud(match, ctx):
    if "log" in ctx: ctx["log"].append("Releasing Spore Cloud.")
