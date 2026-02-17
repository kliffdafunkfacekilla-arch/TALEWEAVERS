def handle_light(match, ctx):
    if "log" in ctx: ctx["log"].append("Creates Light.")

def handle_darkvision(match, ctx):
    user = ctx.get("attacker")
    if user:
        if "log" in ctx: ctx["log"].append(f"{user.name} gains Darkvision.")

def handle_see_invis(match, ctx):
    user = ctx.get("attacker")
    if user:
        if "log" in ctx: ctx["log"].append(f"{user.name} can See Invisibility.")

def handle_xray(match, ctx):
    if "log" in ctx: ctx["log"].append("X-Ray Vision Active.")

def handle_gps(match, ctx):
    if "log" in ctx: ctx["log"].append("Knows exact location.")

def handle_scry(match, ctx):
    if "log" in ctx: ctx["log"].append("Remote Viewing active.")

def handle_postcognition(match, ctx):
    if "log" in ctx: ctx["log"].append("Viewing the Past.")

def handle_identify(match, ctx):
    if "log" in ctx: ctx["log"].append("Identifying Item properties.")

def handle_open_mechanism(match, ctx):
    if "log" in ctx: ctx["log"].append("Opening Lock/Mechanism.")

def handle_purify_liquid(match, ctx):
    if "log" in ctx: ctx["log"].append("Purifying Liquid.")

def handle_unmix_potion(match, ctx):
    if "log" in ctx: ctx["log"].append("Un-mixing Compound.")

def handle_create_gold(match, ctx):
    if "log" in ctx: ctx["log"].append("Transmuting to Gold!")

def handle_transmute(match, ctx):
    if "log" in ctx: ctx["log"].append("Transmuting Material.")

def handle_repair(match, ctx):
    if "log" in ctx: ctx["log"].append("Repairing Item.")

def handle_forge(match, ctx):
    if "log" in ctx: ctx["log"].append("Forging Weapon.")

def handle_shape_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Shaping Matter.")

def handle_fuse_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Fusing Matter.")

def handle_liquify(match, ctx):
    if "log" in ctx: ctx["log"].append("Turning solid to liquid.")

def handle_mist_form(match, ctx):
    if "log" in ctx: ctx["log"].append("Assuming Mist Form.")

def handle_create_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Matter from nothing.")
    
def handle_disintegrate_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Disintegrating Matter.")

def handle_create_life(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Lifeform.")

def handle_detect_life(match, ctx):
    if "log" in ctx: ctx["log"].append("Detecting Life.")

def handle_tremorsense(match, ctx):
    if "log" in ctx: ctx["log"].append("Tremorsense Active.")

def handle_biosense(match, ctx):
    if "log" in ctx: ctx["log"].append("Bio-Sense Active.")

def handle_thermal_sight(match, ctx):
    if "log" in ctx: ctx["log"].append("Thermal Sight Active.")

def handle_omnivision(match, ctx):
    if "log" in ctx: ctx["log"].append("Omni-Vision (Cannot be Flanked).")

def handle_enhanced_hearing(match, ctx):
    if "log" in ctx: ctx["log"].append("Enhanced Hearing.")

def handle_mimicry(match, ctx):
    if "log" in ctx: ctx["log"].append("Mimicking sound/voice.")

def handle_goodberry(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Goodberry (Heal Item).")

def handle_narrative_benefit(match, ctx):
    # Catch-all for flavor
    pass

def handle_search(match, ctx):
    if "log" in ctx: ctx["log"].append("Searching area...")

def handle_rest(match, ctx):
    if "log" in ctx: ctx["log"].append("Resting...")

def handle_invisibility(match, ctx):
    user = ctx.get("attacker")
    if user:
        if hasattr(user, "apply_effect"): user.apply_effect("Invisible", 3)
        if "log" in ctx: ctx["log"].append(f"{user.name} turns Invisible.")

def handle_disguise(match, ctx):
    if "log" in ctx: ctx["log"].append("Disguising Self.")

def handle_camo(match, ctx):
    if "log" in ctx: ctx["log"].append("Camouflaging.")

def handle_illusion(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Illusion.")

def handle_major_image(match, ctx):
    if "log" in ctx: ctx["log"].append("Creating Major Image.")

def handle_hidden_reality(match, ctx):
    if "log" in ctx: ctx["log"].append("Hiding from Reality.")

def handle_speak_dead(match, ctx):
    if "log" in ctx: ctx["log"].append("Speaking with Dead.")

def handle_augury(match, ctx):
    if "log" in ctx: ctx["log"].append("Reading the Future.")

def handle_tongues(match, ctx):
    if "log" in ctx: ctx["log"].append("Speaking Tongues.")

def handle_locate(match, ctx):
    if "log" in ctx: ctx["log"].append("Locating Object.")

def handle_water_breathing(match, ctx):
    if "log" in ctx: ctx["log"].append("Water Breathing Active.")

def handle_hold_breath(match, ctx):
    if "log" in ctx: ctx["log"].append("Holding Breath.")

def handle_flavor_text(match, ctx):
    pass

def handle_lift(match, ctx):
    if "log" in ctx: ctx["log"].append("Lifting Object (Reduce Weight).")

def handle_burden(match, ctx):
    target = ctx.get("target")
    if target: 
         if "log" in ctx: ctx["log"].append(f"{target.name} Burdened (Slowed).")
         # Logic to reduce speed would go here

def handle_breach(match, ctx):
    if "log" in ctx: ctx["log"].append("Breaching Cover/Wall!")

def handle_gravity_well(match, ctx):
    if "log" in ctx: ctx["log"].append("Gravity Well created.")

def handle_feather_fall(match, ctx):
    if "log" in ctx: ctx["log"].append("Feather Fall (Slow Fall).")

def handle_preserve(match, ctx):
    if "log" in ctx: ctx["log"].append("Preserving Object (Stop Decay).")

def handle_arcane_lock(match, ctx):
    if "log" in ctx: ctx["log"].append("Arcane Lock (Unopenable).")

def handle_aura_courage(match, ctx):
    if "log" in ctx: ctx["log"].append("Aura of Courage (Immune to Fear).")

def handle_ward(match, ctx):
    if "log" in ctx: ctx["log"].append("Warding Bond (Share Damage/Buff AC).")

def handle_reveal(match, ctx):
    if "log" in ctx: ctx["log"].append("Revealing Invisibility/Stealth.")

def handle_sanctuary(match, ctx):
    if "log" in ctx: ctx["log"].append("Sanctuary (Enemies must save to attack).")

def handle_dazzle(match, ctx):
    if "log" in ctx: ctx["log"].append("Dazzled! (Blind/Stun).")
