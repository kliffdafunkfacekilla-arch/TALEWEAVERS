def handle_action_economy(match, ctx):
    if "log" in ctx: ctx["log"].append("Modifying Action Economy.")

def handle_mechanic_flag(match, ctx):
    flag = match.group(0)
    if "log" in ctx: ctx["log"].append(f"Flag Set: {flag}")

def handle_skill_buff(match, ctx):
    if "log" in ctx: ctx["log"].append("Skill Buff Applied.")

def handle_skill_advantage(match, ctx):
    if "log" in ctx: ctx["log"].append("Skill Advantage Applied.")
    if "advantage" in ctx: ctx["advantage"] = True

def handle_stat_buff(match, ctx):
    stat = match.group(1)
    if "log" in ctx: ctx["log"].append(f"Stat Buff ({stat}): Gains Advantage.")
    if "advantage" in ctx: ctx["advantage"] = True

def handle_stat_drain(match, ctx):
    if "log" in ctx: ctx["log"].append("Stat Drained: Gains Disadvantage.")
    if "disadvantage" in ctx: ctx["disadvantage"] = True

def handle_natural_armor_buff(match, ctx):
    if "log" in ctx: ctx["log"].append("Natural Armor Buff.")

def handle_talent_reroll(match, ctx):
    if "log" in ctx: ctx["log"].append("Talent: Reroll available.")

def handle_force_reroll(match, ctx):
    if "log" in ctx: ctx["log"].append("Forcing Reroll.")

def handle_lucky(match, ctx):
    if "log" in ctx: ctx["log"].append("Lucky: Reroll 1s.")

def handle_auto_nat20(match, ctx):
    if "log" in ctx: ctx["log"].append("Omen: Auto Natural 20.")

def handle_divine_save(match, ctx):
    if "log" in ctx: ctx["log"].append("Divine Auto-Save.")

def handle_initiative_talent(match, ctx):
    if "log" in ctx: ctx["log"].append("Initiative Bonus.")

def handle_crit_expand(match, ctx):
    if "log" in ctx: ctx["log"].append("Critical Range Expanded.")

def handle_crit_range_19(match, ctx):
    if "log" in ctx: ctx["log"].append("Crit on 19-20.")
    if "crit_threshold" in ctx: ctx["crit_threshold"] = 19

def handle_piercing_crit(match, ctx):
    if "log" in ctx: ctx["log"].append("Piercing Critical Bonus.")

def handle_conditional_advantage(match, ctx):
    if "log" in ctx: ctx["log"].append("Conditional Advantage.")

def handle_advantage(match, ctx):
    if "advantage" in ctx: ctx["advantage"] = True
    if "log" in ctx: ctx["log"].append("Advantage Applied.")

def handle_disadvantage(match, ctx):
    if "disadvantage" in ctx: ctx["disadvantage"] = True
    if "log" in ctx: ctx["log"].append("Disadvantage Applied.")

def handle_die_hit_bonus(match, ctx):
    if "log" in ctx: ctx["log"].append("Bonus Die to Hit (Converted to Advantage).")
    if "advantage" in ctx: ctx["advantage"] = True

def handle_die_hit_penalty(match, ctx):
    if "log" in ctx: ctx["log"].append("Penalty Die to Hit (Converted to Disadvantage).")
    if "disadvantage" in ctx: ctx["disadvantage"] = True

def handle_to_hit_bonus(match, ctx):
    val = int(match.group(1))
    if "log" in ctx: ctx["log"].append(f"+{val} to Hit (Converted to Advantage).")
    if "advantage" in ctx: ctx["advantage"] = True

def handle_to_hit_penalty(match, ctx):
    val = int(match.group(1))
    if "log" in ctx: ctx["log"].append(f"-{val} to Hit (Converted to Disadvantage).")
    if "disadvantage" in ctx: ctx["disadvantage"] = True

def handle_time_stop(match, ctx):
    if "log" in ctx: ctx["log"].append("Time Stop Active.")

def handle_reset_round(match, ctx):
    if "log" in ctx: ctx["log"].append("Resetting Round.")

def handle_retcon_save(match, ctx):
    if "log" in ctx: ctx["log"].append("Retcon/Reload Save.")

def handle_predict_future(match, ctx):
    if "log" in ctx: ctx["log"].append("Predicting Future.")

def handle_double_turn(match, ctx):
    if "log" in ctx: ctx["log"].append("Double Turn.")

def handle_delay_turn(match, ctx):
    if "log" in ctx: ctx["log"].append("Delaying Enemy Turn.")

def handle_infinite_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Infinite Attacks.")

def handle_ignore_resistance(match, ctx):
    if "log" in ctx: ctx["log"].append("Ignoring Resistance.")

def handle_ignore_ac_bonuses(match, ctx):
    if "log" in ctx: ctx["log"].append("Ignoring AC Bonuses.")

def handle_ignore_cover(match, ctx):
    if "ignore_cover" in ctx: ctx["ignore_cover"] = True
    if "log" in ctx: ctx["log"].append("Ignoring Cover.")

def handle_ignore_armor(match, ctx):
    if "log" in ctx: ctx["log"].append("Ignoring Armor.")

def handle_weak_point(match, ctx):
    if "log" in ctx: ctx["log"].append("Targeting Weak Point.")

def handle_true_strike(match, ctx):
    if "log" in ctx: ctx["log"].append("True Strike (+Hit).")

def handle_cost(match, ctx):
    amt = int(match.group(1))
    res_type = match.group(2).upper()
    
    user = ctx.get("attacker")
    if not user: return 
    
    current_val = 0
    if res_type == "SP": current_val = user.sp 
    elif res_type == "FP": current_val = user.fp
    elif res_type == "CMP": current_val = user.cmp
    elif res_type == "HP": current_val = user.hp
    
    if current_val < amt:
        if "log" in ctx: ctx["log"].append(f"Not enough {res_type}! Need {amt}.")
        raise Exception(f"Insufficient {res_type}")
        
    if res_type == "SP": user.sp -= amt
    elif res_type == "FP": user.fp -= amt
    elif res_type == "CMP": user.cmp -= amt
    elif res_type == "HP": user.hp -= amt
    
    if "log" in ctx: ctx["log"].append(f"Consumed {amt} {res_type}")

def handle_counterspell(match, ctx):
    if "log" in ctx: ctx["log"].append("Counterspell!")

def handle_antimagic(match, ctx):
    if "log" in ctx: ctx["log"].append("Antimagic Zone!")

def handle_drain_magic(match, ctx):
    if "log" in ctx: ctx["log"].append("Draining Magic Slots.")

def handle_prevent_lying(match, ctx):
    if "log" in ctx: ctx["log"].append("Zone of Truth.")

def handle_force_speech(match, ctx):
    if "log" in ctx: ctx["log"].append("Compelled Speech.")

def handle_banishment(match, ctx):
    if "log" in ctx: ctx["log"].append("Banishing Target.")

def handle_power_word_kill(match, ctx):
    if "log" in ctx: ctx["log"].append("Power Word Kill.")

def handle_new_law(match, ctx):
    if "log" in ctx: ctx["log"].append("Setting New Physics Law.")

def handle_jinx(match, ctx):
    if "log" in ctx: ctx["log"].append("Jinx!")

def handle_bless(match, ctx):
    if "log" in ctx: ctx["log"].append("Bless!")

def handle_curse(match, ctx):
    if "log" in ctx: ctx["log"].append("Curse applied.")

def handle_fate(match, ctx):
    if "log" in ctx: ctx["log"].append("Fate Intervention.")

def handle_coin_flip(match, ctx):
    if "log" in ctx: ctx["log"].append("Coin Flip...")

def handle_gamble(match, ctx):
    if "log" in ctx: ctx["log"].append("Gambling Effect.")

def handle_serendipity(match, ctx):
    if "log" in ctx: ctx["log"].append("Serendipity!")

def handle_doom(match, ctx):
    if "log" in ctx: ctx["log"].append("DOOM.")

def handle_weapon_tag(match, ctx):
    if "log" in ctx: ctx["log"].append(f"Weapon Trait: {match.group(1)}")

def handle_armor_tag(match, ctx):
    if "log" in ctx: ctx["log"].append("Armor Trait applied.")

def handle_movement_cheat(match, ctx):
    if "log" in ctx: ctx["log"].append("Ignoring Terrain.")

def handle_apply_burning(match, ctx):
     # Status but triggered as meta effect/tag
     if "log" in ctx: ctx["log"].append("Apply Burning Tag.")

def handle_apply_frozen(match, ctx):
     if "log" in ctx: ctx["log"].append("Apply Frozen Tag.")

def handle_apply_staggered(match, ctx):
     if "log" in ctx: ctx["log"].append("Apply Staggered Tag.")

def handle_apply_bleeding(match, ctx):
     if "log" in ctx: ctx["log"].append("Apply Bleeding Tag.")

def handle_auto_crit(match, ctx):
     if "log" in ctx: ctx["log"].append("Next hit is Auto-Crit.")

def handle_damage_reduction(match, ctx):
     if "log" in ctx: ctx["log"].append("Damage Reduction applied.")
     
def handle_damage_vs_armor(match, ctx):
     if "log" in ctx: ctx["log"].append("Bonus Damage vs Armor.")

def handle_knockback_talent(match, ctx):
     if "log" in ctx: ctx["log"].append("Knockback Talent.")

def handle_pierce_talent(match, ctx):
     if "log" in ctx: ctx["log"].append("Piercing Talent.")

def handle_sunder_talent(match, ctx):
     if "log" in ctx: ctx["log"].append("Sunder Talent.")

def handle_confused(match, ctx):
     if "log" in ctx: ctx["log"].append("Confused (Attack Ally).")

def handle_berserk(match, ctx):
     if "log" in ctx: ctx["log"].append("Berserk Mode.")

def handle_taunt(match, ctx):
     if "log" in ctx: ctx["log"].append("Taunted.")
     
def handle_sanctuary(match, ctx):
     if "log" in ctx: ctx["log"].append("Sanctuary.")

def handle_chain_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Chain Attack.")

def handle_temp_ac_advantage(match, ctx):
    if "log" in ctx: ctx["log"].append("Temp AC Advantage.")

def handle_line_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Line Attack.")

def handle_redirect(match, ctx):
    if "log" in ctx: ctx["log"].append("Redirect Attack.")

def handle_aoe_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Attack All Enemies.")

def handle_multihit(match, ctx):
    if "log" in ctx: ctx["log"].append("Multi-Hit.")

def handle_multihit_barrage(match, ctx):
    if "log" in ctx: ctx["log"].append("Barrage.")

def handle_aging(match, ctx):
    if "log" in ctx: ctx["log"].append("Rapid Aging.")

def handle_reflect(match, ctx):
    if "log" in ctx: ctx["log"].append("Reflect.")

def handle_reactive_move(match, ctx):
    if "log" in ctx: ctx["log"].append("Reactive Move.")

def handle_death_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Death Throes Attack.")

def handle_cleave(match, ctx):
    if "log" in ctx: ctx["log"].append("Cleave (Two Targets).")

def handle_reach(match, ctx):
    if "log" in ctx: ctx["log"].append("Extended Reach.")

def handle_alert(match, ctx):
    if "log" in ctx: ctx["log"].append("Cannot be Surprised.")
    
def handle_create_item_fruit(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Fruit.")
    
def handle_obscurement(match, ctx):
    if "log" in ctx: ctx["log"].append("Heavily Obscured.")
    
def handle_breathe_water(match, ctx):
    if "log" in ctx: ctx["log"].append("Breathe Water.")

def handle_analyze(match, ctx):
    if "log" in ctx: ctx["log"].append("Analyze Stats.")

def handle_aoe_push(match, ctx):
    if "log" in ctx: ctx["log"].append("AOE Push.")

def handle_aoe_shape(match, ctx):
    if "log" in ctx: ctx["log"].append(f"AOE Shape: {match.group(0)}")

def handle_aoe_targets(match, ctx):
    if "log" in ctx: ctx["log"].append(f"AOE Targets: {match.group(0)}")

def handle_ethereal(match, ctx):
    if "log" in ctx: ctx["log"].append("Ethereal.")

def handle_phase(match, ctx):
    if "log" in ctx: ctx["log"].append("Phasing.")

def handle_amorphous(match, ctx):
    if "log" in ctx: ctx["log"].append("Amorphous.")

def handle_displacement(match, ctx):
    if "log" in ctx: ctx["log"].append("Displacement.")

def handle_disintegrate(match, ctx):
    if "log" in ctx: ctx["log"].append("Disintegrate.")

def handle_sever_limb(match, ctx):
    if "log" in ctx: ctx["log"].append("Sever Limb.")

def handle_compress_space(match, ctx):
    if "log" in ctx: ctx["log"].append("Compress Space.")

def handle_find_path(match, ctx):
    if "log" in ctx: ctx["log"].append("Find Path.")

def handle_disarm(match, ctx):
    if "log" in ctx: ctx["log"].append("Disarm.")

def handle_snatch_projectile(match, ctx):
    if "log" in ctx: ctx["log"].append("Snatch Projectile.")

def handle_steal_item(match, ctx):
    if "log" in ctx: ctx["log"].append("Steal Item.")

def handle_switch_items(match, ctx):
    if "log" in ctx: ctx["log"].append("Switch Items.")

def handle_precision_knockdown(match, ctx):
    if "log" in ctx: ctx["log"].append("Precision Knockdown.")

def handle_reduce_melee_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Reduce Melee Damage.")

def handle_crit_range_19(match, ctx):
    if "log" in ctx: ctx["log"].append("Crit Range 19.")

def handle_attack_adjacent(match, ctx):
    if "log" in ctx: ctx["log"].append("Attack Adjacent.")

def handle_flanking_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Flanking Bonus.")

def handle_opportunity_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Opportunity Attack.")

def handle_rally_allies(match, ctx):
    if "log" in ctx: ctx["log"].append("Rally Allies.")

def handle_mobile_shooter(match, ctx):
    if "log" in ctx: ctx["log"].append("Mobile Shooter (No Penalty).")

def handle_tail_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Tail Attack.")

def handle_water_stability(match, ctx):
    if "log" in ctx: ctx["log"].append("Water Stability.")

def handle_speed_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Damage based on Speed.")

def handle_quick_attack(match, ctx):
    if "log" in ctx: ctx["log"].append("Quick Attack.")

def handle_self_hit(match, ctx):
    if "log" in ctx: ctx["log"].append("Hit Self.")

def handle_miss_ally(match, ctx):
    if "log" in ctx: ctx["log"].append("Miss hits Ally.")

def handle_unhealable_wound(match, ctx):
    if "log" in ctx: ctx["log"].append("Wound cannot be healed.")

def handle_headbutt(match, ctx):
    if "log" in ctx: ctx["log"].append("Headbutt.")

def handle_luck_trip(match, ctx):
    if "log" in ctx: ctx["log"].append("Trip (Bad Luck).")

def handle_weapon_jam(match, ctx):
    if "log" in ctx: ctx["log"].append("Weapon Jam.")

def handle_fumble(match, ctx):
    if "log" in ctx: ctx["log"].append("Fumble.")

def handle_backfire(match, ctx):
    if "log" in ctx: ctx["log"].append("Backfire.")

def handle_ricochet(match, ctx):
    if "log" in ctx: ctx["log"].append("Ricochet.")

def handle_calamity(match, ctx):
    if "log" in ctx: ctx["log"].append("Calamity.")

def handle_miracle(match, ctx):
    if "log" in ctx: ctx["log"].append("Miracle.")

def handle_karma(match, ctx):
    if "log" in ctx: ctx["log"].append("Karma.")
    
def handle_best_route(match, ctx):
    if "log" in ctx: ctx["log"].append("Best Route.")

def handle_stop_heart(match, ctx):
    if "log" in ctx: ctx["log"].append("Stop Heart.")

def handle_infinite_stamina(match, ctx):
    if "log" in ctx: ctx["log"].append("Infinite Stamina.")

def handle_shatter(match, ctx):
    if "log" in ctx: ctx["log"].append("Shatter Object.")

def handle_indestructible(match, ctx):
    if "log" in ctx: ctx["log"].append("Indestructible.")

def handle_harden_skin(match, ctx):
    if "log" in ctx: ctx["log"].append("Harden Skin.")
    
def handle_shape_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Shape Matter.")

def handle_resist_elements(match, ctx):
    if "log" in ctx: ctx["log"].append("Resist Elements.")
    
def handle_fuse_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Fuse Matter.")

def handle_rust(match, ctx):
    if "log" in ctx: ctx["log"].append("Rust Metal.")

def handle_extinguish(match, ctx):
    if "log" in ctx: ctx["log"].append("Extinguish Fire.")

def handle_transmute(match, ctx):
    if "log" in ctx: ctx["log"].append("Transmute.")

def handle_bounce_physical(match, ctx):
    if "log" in ctx: ctx["log"].append("Bounce Physical.")

def handle_reflect_ray(match, ctx):
    if "log" in ctx: ctx["log"].append("Reflect Ray.")

def handle_black_hole(match, ctx):
    if "log" in ctx: ctx["log"].append("Black Hole.")

def handle_erase_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Erase Matter.")

def handle_reverse_gravity(match, ctx):
    if "log" in ctx: ctx["log"].append("Reverse Gravity.")

def handle_force_field(match, ctx):
    if "log" in ctx: ctx["log"].append("Force Field.")

def handle_teleport_gate(match, ctx):
    if "log" in ctx: ctx["log"].append("Teleport Gate.")

def handle_identify(match, ctx):
    if "log" in ctx: ctx["log"].append("Identify.")

def handle_nondetection(match, ctx):
    if "log" in ctx: ctx["log"].append("Nondetection.")

def handle_silence(match, ctx):
     if "log" in ctx: ctx["log"].append("Silencing Area.")

def handle_tongues(match, ctx):
     if "log" in ctx: ctx["log"].append("Tongues.")

def handle_anchor_space(match, ctx):
     if "log" in ctx: ctx["log"].append("Anchor Space.")

def handle_wish(match, ctx):
     if "log" in ctx: ctx["log"].append("WISH.")

def handle_calculate_defense(match, ctx):
     if "log" in ctx: ctx["log"].append("Calculating Defense.")

def handle_hit_weak_point(match, ctx):
     if "log" in ctx: ctx["log"].append("Hit Weak Point.")

def handle_trap_logic(match, ctx):
     if "log" in ctx: ctx["log"].append("Logic Trap.")

def handle_deconstruct_armor(match, ctx):
     if "log" in ctx: ctx["log"].append("Deconstruct Armor.")

def handle_rewrite_physics(match, ctx):
     if "log" in ctx: ctx["log"].append("Rewrite Physics.")

def handle_delete_entity(match, ctx):
     if "log" in ctx: ctx["log"].append("Delete Entity.")

def handle_psychic_damage(match, ctx):
     if "log" in ctx: ctx["log"].append("Psychic Damage.")
     
def handle_calm_emotions(match, ctx):
     if "log" in ctx: ctx["log"].append("Calm Emotions.")

def handle_empathy_link(match, ctx):
     if "log" in ctx: ctx["log"].append("Empathy Link.")

def handle_flee_fear(match, ctx):
     if "log" in ctx: ctx["log"].append("Flee due to Fear.")

def handle_inspire(match, ctx):
     if "log" in ctx: ctx["log"].append("Inspire.")

def handle_block_path_mental(match, ctx):
     if "log" in ctx: ctx["log"].append("Block Path (Mental).")

def handle_oath_bond(match, ctx):
     if "log" in ctx: ctx["log"].append("Oath / Bond.")
     
def handle_mass_awe(match, ctx):
     if "log" in ctx: ctx["log"].append("Mass Awe.")
     
def handle_reaction_ac(match, ctx):
     if "log" in ctx: ctx["log"].append("Reaction AC.")

def handle_multihit_barrage(match, ctx):
     if "log" in ctx: ctx["log"].append("Barrage.")
     
def handle_teleport_leap(match, ctx):
     if "log" in ctx: ctx["log"].append("Teleport Leap.")

def handle_snatch_missile(match, ctx):
     if "log" in ctx: ctx["log"].append("Snatch Missile.")

def handle_decoy_clones(match, ctx):
     if "log" in ctx: ctx["log"].append("Decoy Clones.")
     
def handle_repeat_action(match, ctx):
     if "log" in ctx: ctx["log"].append("Repeat Action.")

def handle_rapid_aging(match, ctx):
     if "log" in ctx: ctx["log"].append("Rapid Aging.")

def handle_rewind_damage(match, ctx):
     if "log" in ctx: ctx["log"].append("Rewind Damage.")

def handle_phase_reality(match, ctx):
     if "log" in ctx: ctx["log"].append("Phase Reality.")

def handle_gore_charge(match, ctx):
     if "log" in ctx: ctx["log"].append("Gore Charge.")

def handle_lunge_reach(match, ctx):
     if "log" in ctx: ctx["log"].append("Lunge Reach.")
     
def handle_venom_injection(match, ctx):
     if "log" in ctx: ctx["log"].append("Venom Injection.")
     
def handle_trample(match, ctx):
     if "log" in ctx: ctx["log"].append("Trample.")

def handle_grapple_bonus(match, ctx):
     if "log" in ctx: ctx["log"].append("Grapple Bonus.")
     
def handle_cone_attack(match, ctx):
     if "log" in ctx: ctx["log"].append("Cone Attack.")
     
def handle_bleed_dot(match, ctx):
     if "log" in ctx: ctx["log"].append("Bleed DoT.")
     
def handle_auto_grapple(match, ctx):
     if "log" in ctx: ctx["log"].append("Auto Grapple.")
     
def handle_biosense(match, ctx):
     if "log" in ctx: ctx["log"].append("Bio-Sense.")

def handle_thermal_sight(match, ctx):
     if "log" in ctx: ctx["log"].append("Thermal Sight.")

def handle_omnivision(match, ctx):
     if "log" in ctx: ctx["log"].append("Omni-Vision.")
     
def handle_enhanced_hearing(match, ctx):
     if "log" in ctx: ctx["log"].append("Enhanced Hearing.")

def handle_slippery(match, ctx):
     if "log" in ctx: ctx["log"].append("Slippery.")
     
def handle_web_shot(match, ctx):
     if "log" in ctx: ctx["log"].append("Web Shot.")
     
def handle_spore_cloud(match, ctx):
     if "log" in ctx: ctx["log"].append("Spore Cloud.")

def handle_tail_sweep(match, ctx):
     if "log" in ctx: ctx["log"].append("Tail Sweep.")

def handle_gust(match, ctx):
     if "log" in ctx: ctx["log"].append("Gust.")

def handle_solar_beam(match, ctx):
     if "log" in ctx: ctx["log"].append("Solar Beam.")
     
def handle_lockjaw(match, ctx):
     if "log" in ctx: ctx["log"].append("Lockjaw.")

def handle_goodberry(match, ctx):
     if "log" in ctx: ctx["log"].append("Goodberry.")

def handle_mimicry(match, ctx):
     if "log" in ctx: ctx["log"].append("Mimicry.")

def handle_halt_movement(match, ctx):
     if "log" in ctx: ctx["log"].append("Halt Movement.")
     
def handle_hold_door(match, ctx):
     if "log" in ctx: ctx["log"].append("Hold Door.")
     
def handle_trip(match, ctx):
     if "log" in ctx: ctx["log"].append("Trip.")
     
def handle_ignore_needs(match, ctx):
     if "log" in ctx: ctx["log"].append("Ignore Needs.")
     
def handle_create_wall(match, ctx):
     if "log" in ctx: ctx["log"].append("Create Wall.")
     
def handle_anchor(match, ctx):
     if "log" in ctx: ctx["log"].append("Anchor.")
     
def handle_petrify(match, ctx):
     if "log" in ctx: ctx["log"].append("Petrify.")

def handle_temp_hp_buff(match, ctx):
     if "log" in ctx: ctx["log"].append("Temp HP Buff.")

def handle_create_struct(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Structure.")

def handle_stasis(match, ctx):
    if "log" in ctx: ctx["log"].append("Stasis.")

def handle_reflect_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Reflect Damage.")
    
def handle_feign_death(match, ctx):
    if "log" in ctx: ctx["log"].append("Feign Death.")

def handle_invulnerability(match, ctx):
    if "log" in ctx: ctx["log"].append("Invulnerability.")

def handle_fortress(match, ctx):
    if "log" in ctx: ctx["log"].append("Fortress.")

def handle_create_land(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Land.")

def handle_fire_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Fire Damage.")
    
def handle_cold_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Cold Damage.")
    
def handle_lightning_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Lightning Damage.")
    
def handle_acid_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Acid Damage.")
    
def handle_sonic_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Sonic Damage.")
    
def handle_force_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Force Damage.")
    
def handle_nuclear_damage(match, ctx):
    if "log" in ctx: ctx["log"].append("Nuclear Damage.")
    
def handle_disintegrate_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Disintegrate Matter.")
    
def handle_create_matter(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Matter.")
    
def handle_heavy_gravity(match, ctx):
    if "log" in ctx: ctx["log"].append("Heavy Gravity.")
    
def handle_launch(match, ctx):
    if "log" in ctx: ctx["log"].append("Launch.")
    
def handle_climb_speed(match, ctx):
    if "log" in ctx: ctx["log"].append("Climb Speed.")

def handle_dense_skin(match, ctx):
    if "log" in ctx: ctx["log"].append("Dense Skin.")

def handle_crush_grapple(match, ctx):
    if "log" in ctx: ctx["log"].append("Crush Grapple.")
    
def handle_fly_speed(match, ctx):
    if "log" in ctx: ctx["log"].append("Fly Speed.")

def handle_drag_swap(match, ctx):
    if "log" in ctx: ctx["log"].append("Drag Swap.")
    
def handle_create_hazard(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Hazard.")
    
def handle_cleanse(match, ctx):
    if "log" in ctx: ctx["log"].append("Cleanse.")

def handle_magic_missile(match, ctx):
    if "log" in ctx: ctx["log"].append("Magic Missile.")
    
def handle_full_heal(match, ctx):
    if "log" in ctx: ctx["log"].append("Full Heal.")
    
def handle_stop_bleed(match, ctx):
    if "log" in ctx: ctx["log"].append("Stop Bleed.")
    
def handle_cure_disease(match, ctx):
    if "log" in ctx: ctx["log"].append("Cure Disease.")
    
def handle_cure_poison(match, ctx):
    if "log" in ctx: ctx["log"].append("Cure Poison.")
    
def handle_lifesteal(match, ctx):
    if "log" in ctx: ctx["log"].append("Lifesteal.")
    
def handle_life_bond(match, ctx):
    if "log" in ctx: ctx["log"].append("Life Bond.")
    
def handle_auto_life(match, ctx):
    if "log" in ctx: ctx["log"].append("Auto Life.")
    
def handle_resurrect(match, ctx):
    if "log" in ctx: ctx["log"].append("Resurrect.")
    
def handle_consume_ally(match, ctx):
    if "log" in ctx: ctx["log"].append("Consume Ally.")
    
def handle_inflict_disease(match, ctx):
    if "log" in ctx: ctx["log"].append("Inflict Disease.")
    
def handle_necrotic(match, ctx):
    if "log" in ctx: ctx["log"].append("Necrotic.")
    
def handle_massive_dot(match, ctx):
    if "log" in ctx: ctx["log"].append("Massive DoT.")

def handle_contagion(match, ctx):
    if "log" in ctx: ctx["log"].append("Contagion.")
    
def handle_creature_bane(match, ctx):
    if "log" in ctx: ctx["log"].append("Creature Bane.")
    
def handle_enlarge(match, ctx):
    if "log" in ctx: ctx["log"].append("Enlarge.")
    
def handle_grow_appendage(match, ctx):
    if "log" in ctx: ctx["log"].append("Grow Appendage.")
    
def handle_natural_armor(match, ctx):
    if "log" in ctx: ctx["log"].append("Natural Armor.")
    
def handle_swarm_form(match, ctx):
    if "log" in ctx: ctx["log"].append("Swarm Form.")
    
def handle_clone(match, ctx):
    if "log" in ctx: ctx["log"].append("Clone.")
    
def handle_animate_plant(match, ctx):
    if "log" in ctx: ctx["log"].append("Animate Plant.")
    
def handle_create_life(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Life.")
    
def handle_detect_life(match, ctx):
    if "log" in ctx: ctx["log"].append("Detect Life.")
    
def handle_vines(match, ctx):
    if "log" in ctx: ctx["log"].append("Vines.")
    
def handle_laser(match, ctx):
    if "log" in ctx: ctx["log"].append("Laser.")
    
def handle_entomb(match, ctx):
    if "log" in ctx: ctx["log"].append("Entombed! (Buried under earth/ice).")

def handle_crystallize(match, ctx):
    if "log" in ctx: ctx["log"].append("Crystallized! (Target is Fragile).")
    # Logic: Next hit is Crit or Vulnerability?
    if "vulnerable_damage" in ctx: ctx["vulnerable_damage"] = True # Hypothetical flag
    if "log" in ctx: ctx["log"].append("Nova.")
    
def handle_split_beam(match, ctx):
    if "log" in ctx: ctx["log"].append("Split Beam.")
    
def handle_burn_undead(match, ctx):
    if "log" in ctx: ctx["log"].append("Burn Undead.")
    
def handle_light_explosion(match, ctx):
    if "log" in ctx: ctx["log"].append("Light Explosion.")
    
def handle_heat_metal(match, ctx):
    if "log" in ctx: ctx["log"].append("Heat Metal.")
    
def handle_see_invis(match, ctx):
    if "log" in ctx: ctx["log"].append("See Invis.")
    
def handle_xray(match, ctx):
    if "log" in ctx: ctx["log"].append("X-Ray.")
    
def handle_darkvision(match, ctx):
    if "log" in ctx: ctx["log"].append("Darkvision.")
    
def handle_gps(match, ctx):
    if "log" in ctx: ctx["log"].append("GPS.")
    
def handle_postcognition(match, ctx):
    if "log" in ctx: ctx["log"].append("Postcognition.")
    
def handle_scry(match, ctx):
    if "log" in ctx: ctx["log"].append("Scry.")
    
def handle_bonus_perception(match, ctx):
    if "log" in ctx: ctx["log"].append("Bonus Perception.")
    
def handle_blindness(match, ctx):
    if "log" in ctx: ctx["log"].append("Blindness.")
    
def handle_perm_blind(match, ctx):
    if "log" in ctx: ctx["log"].append("Perm Blind.")
    
def handle_dazzle(match, ctx):
    if "log" in ctx: ctx["log"].append("Dazzle.")
    
def handle_block_sight(match, ctx):
    if "log" in ctx: ctx["log"].append("Block Sight.")
    
def handle_invisibility(match, ctx):
    if "log" in ctx: ctx["log"].append("Invisibility.")
    
def handle_disguise(match, ctx):
    if "log" in ctx: ctx["log"].append("Disguise.")
    
def handle_camo(match, ctx):
    if "log" in ctx: ctx["log"].append("Camo.")
    
def handle_illusion(match, ctx):
    if "log" in ctx: ctx["log"].append("Illusion.")
    
def handle_major_image(match, ctx):
    if "log" in ctx: ctx["log"].append("Major Image.")
    
def handle_hidden_reality(match, ctx):
    if "log" in ctx: ctx["log"].append("Hidden Reality.")
    
def handle_squeeze(match, ctx):
    if "log" in ctx: ctx["log"].append("Squeeze.")
    
def handle_wall_walk(match, ctx):
    if "log" in ctx: ctx["log"].append("Wall Walk.")
    
def handle_tremorsense(match, ctx):
    if "log" in ctx: ctx["log"].append("Tremorsense.")
    
def handle_immovable(match, ctx):
    if "log" in ctx: ctx["log"].append("Immovable.")
    
def handle_withdraw(match, ctx):
    if "log" in ctx: ctx["log"].append("Withdraw.")

def handle_create_terrain(match, ctx):
    if "log" in ctx: ctx["log"].append("Create Terrain.")
    
def handle_levitate(match, ctx):
    if "log" in ctx: ctx["log"].append("Levitate.")

def handle_save_condition(match, ctx):
     if "log" in ctx: ctx["log"].append("Save Condition.")

def handle_save_push(match, ctx):
     if "log" in ctx: ctx["log"].append("Save Push.")

def handle_save_half_damage(match, ctx):
     if "log" in ctx: ctx["log"].append("Save Half Damage.")

def handle_save_damage(match, ctx):
     if "log" in ctx: ctx["log"].append("Save Damage.")

# --- ANUMIS HANDLERS ---
def handle_regenerate(match, ctx):
    if "log" in ctx: ctx["log"].append("Regenerate (Heal per turn).")

def handle_soul_trap(match, ctx):
    if "log" in ctx: ctx["log"].append("Soul Trapped! (Cannot Revive).")

def handle_blight(match, ctx):
    if "log" in ctx: ctx["log"].append("Blighted (Wither Area).")

def handle_exhaustion(match, ctx):
    if "log" in ctx: ctx["log"].append("Exhaustion Level Increased.")

def handle_create_homunculus(match, ctx):
    if "log" in ctx: ctx["log"].append("Created Homunculus Servant.")

def handle_life_link(match, ctx):
    if "log" in ctx: ctx["log"].append("Life Link (Share Damage).")

# --- RATIO HANDLERS ---
def handle_logic_bomb(match, ctx):
    if "log" in ctx: ctx["log"].append("Logic Bomb (AOE Stun/Psychic).")

def handle_edit_memory(match, ctx):
    if "log" in ctx: ctx["log"].append("Editing Memory.")

def handle_calculate(match, ctx):
    if "log" in ctx: ctx["log"].append("Calculated Outcome (Auto-Hit).")
    if "advantage" in ctx: ctx["advantage"] = True

def handle_mind_read(match, ctx):
    if "log" in ctx: ctx["log"].append("Reading Mind (Detect Intent).")
    
def handle_encrypt(match, ctx):
    if "log" in ctx: ctx["log"].append("Encrypting Info (Cannot be Read).")

def handle_charm(match, ctx):
    if "log" in ctx: ctx["log"].append("Charmed (Friendly).")
    
def handle_fear(match, ctx):
    if "log" in ctx: ctx["log"].append("Fear (Frightened).")

def handle_forbid(match, ctx):
    if "log" in ctx: ctx["log"].append("Forbid Action (Cannot do X).")

def handle_true_name(match, ctx):
    if "log" in ctx: ctx["log"].append("Invoking True Name (Full Control/Crit).")

def handle_new_law(match, ctx):
    if "log" in ctx: ctx["log"].append("Proclaiming New Law (Global Rule).")

def handle_prevent_lying(match, ctx):
    if "log" in ctx: ctx["log"].append("Zone of Truth (Cannot Lie).")

def handle_force_speech(match, ctx):
    if "log" in ctx: ctx["log"].append("Command/Force Speech.")
    
def handle_silence(match, ctx):
    if "log" in ctx: ctx["log"].append("Silence (No Spells/Speech).")
    
def handle_bless(match, ctx):
    if "log" in ctx: ctx["log"].append("Bless (+1d4).")

def handle_divine_save(match, ctx):
     if "log" in ctx: ctx["log"].append("Divine Save.")
