import re
import random
# Import mechanics modules
from .mechanics import damage, status, healing, movement, defense, utility, summoning, meta

class EffectRegistry:
    def __init__(self):
        # List of (regex_pattern, handler_function)
        self.patterns = []
        self._register_defaults()

    def register_pattern(self, regex, handler):
        self.patterns.append((re.compile(regex, re.IGNORECASE), handler))

    def resolve(self, effect_desc, context):
        """
        Attempts to resolve an effect description into an action.
        context: dict containing 'attacker', 'target', 'engine', 'damage', etc.
        """
        if not effect_desc: return False
        
        handled = False
        for pattern, handler in self.patterns:
            match = pattern.search(effect_desc)
            if match:
                # Pass match groups + context to handler
                try:
                    handler(match, context)
                    handled = True
                    # Don't break immediately, allow multiple patterns to match (e.g. Damage + Status)
                    # break 
                except Exception as e:
                    print(f"[EffectRegistry] Error handling '{effect_desc}': {e}")
        
        if not handled:
            # Fallback for logging
            # print(f"[EffectRegistry] Unhandled effect: {effect_desc}")
            pass
        return handled

    def _register_defaults(self):
        # --- DAMAGE ---
        self.register_pattern(r"Deal (\d+)?d?(\d+)? ?(\w+) Damage", damage.handle_deal_damage)
        self.register_pattern(r"(\w+) Damage", damage.handle_simple_damage)
        self.register_pattern(r"Magic Missile|Bolt|Auto hit", damage.handle_magic_missile)
        self.register_pattern(r"Auto-Hit", damage.handle_auto_hit)
        self.register_pattern(r"Auto-Damage|No Roll", damage.handle_auto_damage)
        self.register_pattern(r"Deal Fire Damage|Heat|Burn", damage.handle_fire_damage)
        self.register_pattern(r"Deal Cold Damage|Chill", damage.handle_cold_damage)
        self.register_pattern(r"Deal Lightning Damage|Shock", damage.handle_lightning_damage)
        self.register_pattern(r"Deal Acid Damage|Melt", damage.handle_acid_damage)
        self.register_pattern(r"Deal Force Damage|Explode", damage.handle_force_damage)
        self.register_pattern(r"Deal Sonic Damage|Shatter", damage.handle_sonic_damage)
        self.register_pattern(r"Nuclear Damage|Fission", damage.handle_nuclear_damage)
        self.register_pattern(r"Damage over Time|(?<!Massive )(?<!Rapid )DoT|(?<!Stop )Bleed", damage.handle_dot)
        self.register_pattern(r"Massive.*?DoT|Rot", damage.handle_massive_dot)
        self.register_pattern(r"Split Damage|Divide", damage.handle_split_damage)
        self.register_pattern(r"Reflect Hit", damage.handle_reflect_damage)
        self.register_pattern(r"Damage scales.*?Speed", damage.handle_dot) # Simplified mapping
        
        # --- HEALING & RESTORATION ---
        self.register_pattern(r"Heal (\d+)d?(\d+)? ?(HP)?", healing.handle_heal)
        self.register_pattern(r"Regain (\d+)?d?(\d+)? ?(HP)?", healing.handle_heal)
        self.register_pattern(r"Regain (\d+) (Stamina|Focus|FP|SP)", healing.handle_restore_resource)
        self.register_pattern(r"(?<!Stasis )Temp(?:orary)? HP", healing.handle_temp_hp)
        self.register_pattern(r"Gain Temporary HP|Reinforce", healing.handle_temp_hp_buff)
        self.register_pattern(r"Heal HP every turn|Regenerat", healing.handle_regeneration)
        self.register_pattern(r"Heal minor wounds|Minor Heal", healing.handle_minor_heal)
        self.register_pattern(r"Stasis Heal|Full recovery", healing.handle_full_heal)
        self.register_pattern(r"Stop Bleeding|Clot", healing.handle_stop_bleed)
        self.register_pattern(r"Cure Disease|Immunity", healing.handle_cure_disease)
        self.register_pattern(r"Cure Poison|Antidote", healing.handle_cure_poison)
        self.register_pattern(r"Lifesteal|Heal for Dmg|Drain Life", healing.handle_lifesteal)
        self.register_pattern(r"Life Bond|Share HP", healing.handle_life_bond)
        self.register_pattern(r"Auto-Life|on death", healing.handle_auto_life)
        self.register_pattern(r"Resurrect|Revive|Bring back", healing.handle_resurrect)
        self.register_pattern(r"Eat minion.*?heal|Consume ally", healing.handle_consume_ally)
        
        # --- STATUS & CONTROL ---
        self.register_pattern(r"Stun", status.handle_stun)
        self.register_pattern(r"Paralyze", status.handle_paralyze)
        self.register_pattern(r"(?<!Cure )Poison", status.handle_poison)
        self.register_pattern(r"Fear|Frightened", status.handle_fear)
        self.register_pattern(r"Charm", status.handle_charm)
        self.register_pattern(r"Deafen", status.handle_deafen)
        self.register_pattern(r"Blind foe|Blindness", status.handle_blindness)
        self.register_pattern(r"Permanent Blindness", status.handle_perm_blind)
        self.register_pattern(r"Dazzle|Visual Noise", status.handle_dazzle)
        self.register_pattern(r"Inflict Disease|Plague", status.handle_inflict_disease)
        self.register_pattern(r"Break Mind|Insanity|Shatter", status.handle_insanity)
        self.register_pattern(r"Heasitate|Doubt|Despair", status.handle_hesitate)
        self.register_pattern(r"Attack All|Enrage|Berserk", status.handle_enrage)
        self.register_pattern(r"Befriend|Charm|Love|Permanent Thrall|Mind Control|Dominate", status.handle_dominate_charm)
        self.register_pattern(r"Stop target's heart|Arrest", status.handle_petrify) # Or kill? Mapping to petrify/stun logic for now
        self.register_pattern(r"Turn target to stone|Petrify", status.handle_petrify)
        self.register_pattern(r"Prevent Casting|Silence", status.handle_silence)
        self.register_pattern(r"Panic|Comatose|Sleep|Feign Death", status.handle_sleep)
        self.register_pattern(r"save.*?or.*?(Prone|Frightened|Charmed|Blinded|Paralyzed|Poisoned|Stunned|Restrained|Deafened)", status.handle_save_condition)
        
        # --- MOVEMENT ---
        self.register_pattern(r"Push.*?(\d+)ft|Shove target away|Knockback", movement.handle_push)
        self.register_pattern(r"save.*?or.*?pushed.*?(\d+)ft", movement.handle_save_push)
        self.register_pattern(r"Teleport.*?(\d+)ft", movement.handle_teleport)
        self.register_pattern(r"Fly Speed|Soar|Fragile Speed|True Flight|Control Gravity", movement.handle_fly_speed)
        self.register_pattern(r"Swim Speed|Propel|Paddle", movement.handle_swim_speed)
        self.register_pattern(r"Climb Speed|Climber|Spider Climb|Shift gravity", movement.handle_climb_speed)
        self.register_pattern(r"Burrow Speed|Earth Glide", movement.handle_burrow_speed)
        self.register_pattern(r"Line Charge|Blitz|Charge attack|Gore", movement.handle_charge)
        self.register_pattern(r"5ft Shift|Step|Dash|Haste", movement.handle_dash)
        self.register_pattern(r"Move through enemy|Weave|Pass through", movement.handle_phase_move)
        self.register_pattern(r"Walk through.*?(wall|solid)|Ethereal|Phase", movement.handle_phase_walk)
        self.register_pattern(r"Escape.*?(bindings|grapple|restraints)|Slippery", movement.handle_escape_grapple)
        self.register_pattern(r"Stop target movement|Halt|Stop all momentum", movement.handle_halt_movement)
        self.register_pattern(r"Compress.*?space|Gravity well|Pull enemies|Black Hole", movement.handle_black_hole)
        
        # --- DEFENSE ---
        self.register_pattern(r"Resistance to (\w+)|Resist (\w+)", defense.handle_resistance)
        self.register_pattern(r"Immune to (\w+)|Immune Magic|Immune to All", defense.handle_immunity)
        self.register_pattern(r"Reduce damage.*half", defense.handle_halve_damage)
        self.register_pattern(r"\+(\d+) (AC|Armor Class)|Bonus AC|Harden", defense.handle_ac_buff)
        self.register_pattern(r"Natural Armor.*?(\d+)|Skin becomes Iron|Skin becomes Diamond", defense.handle_ac_buff) # Simplified
        self.register_pattern(r"Immune to Critical|Immune Crits", defense.handle_crit_immunity)
        self.register_pattern(r"shield.*?ally.*?overhead|shield.*?rain", defense.handle_shield_ally)
        self.register_pattern(r"Reaction AC bonus|Duck", defense.handle_reaction_ac)
        self.register_pattern(r"Reduce incoming Physical|Dense", defense.handle_dense_skin)
        self.register_pattern(r"Reflect Ray|Mirror", defense.handle_reflect_ray)
        self.register_pattern(r"Take damage meant for an ally|Absorb", defense.handle_absorb_damage)
        self.register_pattern(r"Absorb All Damage|Void", defense.handle_absorb_all)
        self.register_pattern(r"Absorb Shock|Ground", defense.handle_absorb_shock)
        self.register_pattern(r"Become immovable|Anchor|Ignore Knockback", defense.handle_immovable)
        self.register_pattern(r"Take 0 Damage|Immunity|Invulnerable|Infinite Mass", defense.handle_invulnerability)
        self.register_pattern(r"Withdraw|Shell|Turtle", defense.handle_withdraw)
        
        # --- UTILITY & FLAVOR ---
        self.register_pattern(r"Invisible|Invisibility|Turn Invisible", utility.handle_invisibility)
        self.register_pattern(r"Darkvision|See in Darkness", utility.handle_darkvision)
        self.register_pattern(r"See Invisible|Truesight", utility.handle_see_invis)
        self.register_pattern(r"See Through Walls|X-Ray", utility.handle_xray)
        self.register_pattern(r"Know Location|GPS", utility.handle_gps)
        self.register_pattern(r"Remote Viewing|Scry|Spy on", utility.handle_scry)
        self.register_pattern(r"Postcognition|See Past|Reconstruct", utility.handle_postcognition)
        self.register_pattern(r"Learn item|Identify", utility.handle_identify)
        self.register_pattern(r"Open.*?mechanism|Pick lock|Unlock", utility.handle_open_mechanism)
        self.register_pattern(r"Clean.*?poison|Purify", utility.handle_purify_liquid)
        self.register_pattern(r"Un-mix|Separate compound", utility.handle_unmix_potion)
        self.register_pattern(r"Lead to Gold|Gold", utility.handle_create_gold)
        self.register_pattern(r"Change material|Transmute", utility.handle_transmute)
        self.register_pattern(r"Fix broken item|Repair", utility.handle_repair)
        self.register_pattern(r"Create weapon|Forge", utility.handle_forge)
        self.register_pattern(r"Mold clay|Shape", utility.handle_shape_matter)
        self.register_pattern(r"Weld metal|Fuse", utility.handle_fuse_matter)
        self.register_pattern(r"Turn solid to liquid|Liquify", utility.handle_liquify)
        self.register_pattern(r"Turn solid to gas|Vaporize|Gas|Turn self to Mist", utility.handle_mist_form)
        self.register_pattern(r"Create Matter", utility.handle_create_matter)
        self.register_pattern(r"Disintegrate Matter|Unmake", utility.handle_disintegrate_matter)
        self.register_pattern(r"Create.*?Lifeform|Spawn", utility.handle_create_life)
        self.register_pattern(r"Detect Life|Life Radar", utility.handle_detect_life)
        self.register_pattern(r"Tremorsense|Detect.*?location|Detect moving", utility.handle_tremorsense)
        self.register_pattern(r"Bio-Sense|Heartbeat detection", utility.handle_biosense)
        self.register_pattern(r"Thermal Sight|Heat detection", utility.handle_thermal_sight)
        self.register_pattern(r"Omni-Vision|Peripheral Sight|Cannot be Flanked", utility.handle_omnivision)
        self.register_pattern(r"Eavesdrop|Hearing", utility.handle_enhanced_hearing)
        self.register_pattern(r"Mimicry|Imitate voice", utility.handle_mimicry)
        self.register_pattern(r"Goodberry|Grow fruit", utility.handle_goodberry)
        self.register_pattern(r"(Mastery|Proficiency) of|Action:|Using .*? to", utility.handle_narrative_benefit) # Priority
        self.register_pattern(r"ask the GM|retroactively|merchants?|follower|following|audience|offend|talk in circles|estimate|invent|lying|emotional state|woe or weal|declare.*?fact|helpful|captivate|mimic|balance|footprints|track|shoot objects|store items|use scrolls|social interaction|friendly disposition|not attack you|consumables.*?craft", utility.handle_narrative_benefit)
        self.register_pattern(r"Search|Perception|Scout|Keen eyes|Track", utility.handle_search)
        self.register_pattern(r"Rest|Wait|Camp|Breathe", utility.handle_rest)
        self.register_pattern(r"Alter Self|Disguise", utility.handle_disguise)
        self.register_pattern(r"Blend with surroundings|Camouflage", utility.handle_camo)
        self.register_pattern(r"Hologram|Illusion|Decoy", utility.handle_illusion)
        self.register_pattern(r"Major Image|Fake Terrain", utility.handle_major_image)
        self.register_pattern(r"Hidden from Reality", utility.handle_hidden_reality)
        self.register_pattern(r"Talk to Dead|Spirit", utility.handle_speak_dead)
        self.register_pattern(r"Hint.*?Future|Augury", utility.handle_augury)
        self.register_pattern(r"Speak any language|Tongues", utility.handle_tongues)
        self.register_pattern(r"Locate Object|Find", utility.handle_locate)
        self.register_pattern(r"Breathe underwater|Amphibious|Respire", utility.handle_water_breathing)
        self.register_pattern(r"Hold breath", utility.handle_hold_breath)
        self.register_pattern(r"(?<!Explosion of )(?<!Massive )(?<!Holy )Light", utility.handle_light)
        
        # --- SUMMONING & CREATION ---
        self.register_pattern(r"summon|call|conjure|Call Ally", summoning.handle_summon)
        self.register_pattern(r"create (wall|barrier|cover)|Entomb|Bury target", summoning.handle_create_wall)
        self.register_pattern(r"Create (Wall|Barrier|Zone|Cloud|Fog|Structure|Shelter|Bridge).*?(Fire|Ice|Acid|Stone|Water)?", summoning.handle_create_terrain)
        self.register_pattern(r"Create Automaton|Construct", summoning.handle_create_construct)
        self.register_pattern(r"Animate.*?(Plant|Tree)|Awaken", summoning.handle_animate_plant)
        self.register_pattern(r"Grow spare body|Clone", summoning.handle_clone)
        self.register_pattern(r"Turn into bugs|Swarm form", summoning.handle_swarm_form)
        self.register_pattern(r"Create new land|Foundation", summoning.handle_create_land)
        self.register_pattern(r"Invulnerable Structure|Fortress|Monolith", summoning.handle_fortress)
        self.register_pattern(r"Web Shot|Sticky Net", summoning.handle_web_shot)
        self.register_pattern(r"Spore Cloud|Release spores", summoning.handle_spore_cloud)

        # --- META / GAME RULES ---
        self.register_pattern(r"Reroll.*?(failed|failure|1s|damage|check|save)?", meta.handle_talent_reroll)
        self.register_pattern(r"Force Reroll|Take Low", meta.handle_force_reroll)
        self.register_pattern(r"Reroll 1s|Lucky", meta.handle_lucky)
        self.register_pattern(r"Favor|Auto.*?Natural 20", meta.handle_auto_nat20)
        self.register_pattern(r"Divine|Auto-Save", meta.handle_divine_save)
        self.register_pattern(r"Initiative", meta.handle_initiative_talent)
        self.register_pattern(r"Crit.*?(\d+)|Critical range", meta.handle_crit_expand)
        self.register_pattern(r"crit(?:ical)? (?:hit )?range.*?19", meta.handle_crit_range_19)
        self.register_pattern(r"piercing.*?19|crit.*?19.*?pierc", meta.handle_piercing_crit)
        self.register_pattern(r"Advantage.*?(on|vs|against) (.*)", meta.handle_conditional_advantage)
        
        # Action Economy
        self.register_pattern(r"free action|two actions|reaction|reload.*?action", meta.handle_action_economy)
        
        # Skill/Stat Buffs
        self.register_pattern(r"(Gain|Grant|\+?\d+ to) (Politics|Survival|Nature|Arcana|Religion|History|Streetwise|Medicine|Diplomacy|Intimidation|Bluff|Insight|Perception|Athletics|Acrobatics|Stealth)", meta.handle_skill_buff)
        self.register_pattern(r"Increase (Might|Reflexes|Endurance|Vitality|Fortitude|Knowledge|Logic|Awareness|Intuition|Charm|Willpower|Finesse)", meta.handle_stat_buff)
        self.register_pattern(r"Drain Stat|Weaken", meta.handle_stat_drain)
        self.register_pattern(r"Advantage on (.*) Checks", meta.handle_skill_advantage)
        
        # Hit Modifiers
        self.register_pattern(r"\+(\d+) to Hit", meta.handle_to_hit_bonus)
        self.register_pattern(r"-(\d+) to Hit", meta.handle_to_hit_penalty)
        self.register_pattern(r"True Strike|Bonus to Hit", meta.handle_true_strike)
        self.register_pattern(r"Weak Point|crit bonus", meta.handle_weak_point)
        
        # Time/Meta
        self.register_pattern(r"End Time|Stop|Time Stop", meta.handle_time_stop)
        self.register_pattern(r"Restart the combat|Reset", meta.handle_reset_round)
        self.register_pattern(r"Reload Save|Retcon|Reality", meta.handle_retcon_save)
        self.register_pattern(r"Predict exact future|Timeline", meta.handle_predict_future)
        self.register_pattern(r"Diffecult Terrain|Rubble", summoning.handle_create_terrain) # Moved from Meta to Summoning/Creation
        self.register_pattern(r"Move through|Pass through|Ignore difficult terrain", meta.handle_movement_cheat)
        
        # Costs
        self.register_pattern(r"Cost:? (\d+) (SP|FP|CMP|HP)", meta.handle_cost)
        
        # Rules Lawyers
        self.register_pattern(r"Counter|Stop spell", meta.handle_counterspell)
        self.register_pattern(r"End active spell|Dispel", meta.handle_counterspell)
        self.register_pattern(r"Create Dead Magic|Antimagic", meta.handle_antimagic)
        self.register_pattern(r"Drain Magic slots|Source", meta.handle_drain_magic)
        self.register_pattern(r"Prevent Lying|Zone of Truth", meta.handle_prevent_lying)
        self.register_pattern(r"Force Speech|Speak", meta.handle_force_speech)
        self.register_pattern(r"Send to another plane|Banish", meta.handle_banishment)
        self.register_pattern(r"Power Word Kill|Kill", meta.handle_power_word_kill)
        self.register_pattern(r"New Physics Law|Law", meta.handle_new_law)
        
        # Omen / Luck
        self.register_pattern(r"Jinx|bad luck", meta.handle_jinx)
        self.register_pattern(r"Bless|good luck", meta.handle_bless)
        self.register_pattern(r"Curse|Disadvantage on Rolls", meta.handle_curse)
        self.register_pattern(r"Fate|Advantage on Rolls", meta.handle_fate)
        self.register_pattern(r"Coin Flip|50/50|Guess", meta.handle_coin_flip)
        self.register_pattern(r"Random Buff|Gamble", meta.handle_gamble)
        self.register_pattern(r"Find Loot|Serendipity", meta.handle_serendipity)
        self.register_pattern(r"Doom|Instant Kill", meta.handle_doom)
        
        # Item Tags
        self.register_pattern(r"\b(Reach|Finesse|Thrown|Throwing|Light|Heavy|Massive|Silent|Returning|Returns|Versatile|Two-Handed|Improvised|Concealable|Hidden|Balanced|Precision|Scoped|Weighted|Barbed|Spiked|Firearm|Pistol|Rifle|Scatter)\b", meta.handle_weapon_tag)
        self.register_pattern(r"Stealth Disadvantage|No Swim|Bulky|Noise penalty|Waterproof|Climbing Speed|Polished|Vestment|Robes|Plating|Moss", meta.handle_armor_tag)

        # --- FLUX SCHOOL ---
        self.register_pattern(r"Ignore Armor Rating|Pierce|Bypass Armor", meta.handle_ignore_armor)
        self.register_pattern(r"Dodge|Bonus to AC", defense.handle_ac_buff)
        self.register_pattern(r"Unlock|Open simple mechanism", utility.handle_open_mechanism)
        self.register_pattern(r"Trip|Knock down", meta.handle_trip)
        self.register_pattern(r"Parry", defense.handle_parry)
        self.register_pattern(r"Untie|Escape bindings", movement.handle_escape_grapple)
        self.register_pattern(r"Disarm", meta.handle_disarm)
        self.register_pattern(r"Catch|Grab weapon", defense.handle_catch)
        self.register_pattern(r"Swap|Switch held items", meta.handle_switch_items)
        self.register_pattern(r"Bleed", damage.handle_dot)
        self.register_pattern(r"Deflect", defense.handle_deflect)
        self.register_pattern(r"Guide|Next attack is Auto-Hit", meta.handle_true_strike)
        self.register_pattern(r"Snatch|Steal equipped item", meta.handle_steal_item)
        self.register_pattern(r"Blur|Attacks have Disadvantage", meta.handle_disadvantage) # Disadvantage on incoming
        self.register_pattern(r"Filter|Clean poison", utility.handle_purify_liquid)
        self.register_pattern(r"Sever|Cut off a limb", meta.handle_sever_limb)
        self.register_pattern(r"Flow|Move .*? when hit", defense.handle_flow)
        self.register_pattern(r"Phase|Walk through solid", movement.handle_phase_walk)
        self.register_pattern(r"Needle|Line attack", meta.handle_line_attack)
        self.register_pattern(r"Ghost|Become Ethereal", meta.handle_ethereal)
        self.register_pattern(r"Ricochet", meta.handle_ricochet)
        self.register_pattern(r"Displace|appear .*? from real spot", meta.handle_displacement)
        self.register_pattern(r"Navigate|Find path", meta.handle_find_path)
        self.register_pattern(r"Atomize|Disintegrate target", meta.handle_disintegrate)
        self.register_pattern(r"Liquid|Amorphous", defense.handle_amorphous)
        self.register_pattern(r"Separate|Un-mix", utility.handle_unmix_potion)
        self.register_pattern(r"Perfect|Auto-Critical Hit", meta.handle_auto_crit)
        self.register_pattern(r"Intangible|Permanent Phasing", defense.handle_intangible)
        self.register_pattern(r"Singularity|Compress space", meta.handle_compress_space)

        # --- MASS SCHOOL ---
        self.register_pattern(r"Push|Shove target|Knockback", movement.handle_push)
        self.register_pattern(r"Brace|Ignore Knockback|Prone effects", defense.handle_brace)
        self.register_pattern(r"Lift|Reduce the weight", utility.handle_lift)
        self.register_pattern(r"Pull|Drag target", movement.handle_pull)
        self.register_pattern(r"Catch|time Stop a physical projectile", defense.handle_catch) # Flux catch covers this too
        self.register_pattern(r"Jump|Boost jump", movement.handle_jump_boost)
        self.register_pattern(r"Slam|Knock .*? Prone", meta.handle_knockback_talent)
        self.register_pattern(r"Repel|Deflect arrows", defense.handle_deflect)
        self.register_pattern(r"Burden|Increase weight|Slow", utility.handle_burden)
        self.register_pattern(r"Crush|Squeeze target|Grapple", meta.handle_crush_grapple)
        self.register_pattern(r"Dense|Reduce incoming Physical", defense.handle_dense_skin)
        self.register_pattern(r"Climb|Spider Climb|Shift gravity", movement.handle_climb_speed)
        self.register_pattern(r"Launch|Fling enemy", movement.handle_launch)
        self.register_pattern(r"Orbit|Shield of debris", defense.handle_orbit)
        self.register_pattern(r"Feather|Slow Fall", utility.handle_feather_fall)
        self.register_pattern(r"Breach|Destroy cover", utility.handle_breach)
        self.register_pattern(r"Heavy|cannot be moved", defense.handle_immovable)
        self.register_pattern(r"Float|Levitate", movement.handle_levitate)
        self.register_pattern(r"Flatten|Compress target", meta.handle_compress_space)
        self.register_pattern(r"Nullify|Stop all momentum", meta.handle_halt_movement)
        self.register_pattern(r"Fly|True Flight|Control Gravity", movement.handle_fly_speed)
        self.register_pattern(r"Implode|Create a vacuum", meta.handle_black_hole)
        self.register_pattern(r"Field|Anti-Gravity Aura", meta.handle_heavy_gravity)
        self.register_pattern(r"Reverse|Flip gravity", movement.handle_reverse_gravity)
        self.register_pattern(r"Meteor|Orbital Strike", damage.handle_force_damage) # High dmg
        self.register_pattern(r"Event Horizon|Absorb incoming magical", defense.handle_event_horizon)
        self.register_pattern(r"Well|Create heavy Gravity Well", utility.handle_gravity_well)
        self.register_pattern(r"Erase|Delete matter", meta.handle_erase_matter)
        self.register_pattern(r"Invincible|Infinite Mass", defense.handle_invulnerability)
        self.register_pattern(r"Black Hole|Consume light", meta.handle_black_hole)

        # --- ORDO SCHOOL ---
        self.register_pattern(r"Halt|Stop target movement", meta.handle_halt_movement) # Ordo 32, 59
        self.register_pattern(r"Stop|End Time", meta.handle_time_stop) # Ordo 59
        self.register_pattern(r"Stand|Stand up from Prone", movement.handle_stand_up)
        self.register_pattern(r"Hold|Keep a door", meta.handle_hold_door)
        self.register_pattern(r"Trip|Create an obstacle", meta.handle_trip)
        self.register_pattern(r"Skin|Natural Armor", defense.handle_natural_armor)
        self.register_pattern(r"Sustain|Ignore hunger", meta.handle_ignore_needs)
        self.register_pattern(r"Trap|Bind target", meta.handle_trap_logic)
        self.register_pattern(r"Anchor|Become immovable", defense.handle_immovable)
        self.register_pattern(r"Bridge|Create a temporary structure", meta.handle_create_struct)
        self.register_pattern(r"Cage|Create walls", meta.handle_create_wall)
        self.register_pattern(r"Barricade|Create cover", meta.handle_create_wall)
        self.register_pattern(r"Preserve|Stop decay", utility.handle_preserve)
        self.register_pattern(r"Petrify|Turn target to stone", status.handle_petrify)
        self.register_pattern(r"Reinforce|Gain Temporary HP", meta.handle_temp_hp_buff)
        self.register_pattern(r"Shelter|Create a safe hut", meta.handle_create_struct)
        self.register_pattern(r"Entomb|Bury target", meta.handle_entomb)
        self.register_pattern(r"Absorb|Take damage for an ally", defense.handle_absorb_damage)
        self.register_pattern(r"Lock|Arcane Lock", utility.handle_arcane_lock)
        self.register_pattern(r"Stasis|Freeze target in time", meta.handle_stasis)
        self.register_pattern(r"Reflect|Return damage", defense.handle_reflect_damage)
        self.register_pattern(r"Statue|Feign Death", meta.handle_feign_death)
        self.register_pattern(r"Arrest|Stop target's heart", meta.handle_stop_heart)
        self.register_pattern(r"Immunity|Take 0 Damage", defense.handle_invulnerability)
        self.register_pattern(r"Stamina|Run forever", meta.handle_infinite_stamina)
        self.register_pattern(r"Crystallize|Make target fragile", meta.handle_crystallize)
        self.register_pattern(r"Fortress|Invulnerable Structure", meta.handle_fortress)
        self.register_pattern(r"Monolith|Create permanent wall", meta.handle_create_wall)
        self.register_pattern(r"Eternal|Cannot die", meta.handle_auto_life)
        self.register_pattern(r"Foundation|Create new land", meta.handle_create_land)

        # --- ANUMIS SCHOOL ---
        self.register_pattern(r"Regenerate|Heal target", meta.handle_regenerate) # Anumis 33
        self.register_pattern(r"Revive|Resurrect target", meta.handle_resurrect) # Anumis 91
        self.register_pattern(r"Life Link|Share damage with", meta.handle_life_link)
        self.register_pattern(r"Cure|Remove Disease|Cleanse", meta.handle_cure_disease)
        self.register_pattern(r"Drain|Lifesteal|Drain HP", meta.handle_lifesteal)
        self.register_pattern(r"Soul Trap|Prevent resurrection", meta.handle_soul_trap)
        self.register_pattern(r"Blight|Wither healing|Reduce Max HP", meta.handle_blight)
        self.register_pattern(r"Exhaust|Apply Exhaustion", meta.handle_exhaustion)
        self.register_pattern(r"Animate|Create Undead", meta.handle_animate_plant) # Adapt for generic
        self.register_pattern(r"Clone|Create Duplicate", meta.handle_clone)
        self.register_pattern(r"Homunculus|Create Servant", meta.handle_create_homunculus)
        self.register_pattern(r"Vines|Entangle target", meta.handle_vines)
        self.register_pattern(r"Spore|Cloud of Poison", meta.handle_spore_cloud)
        self.register_pattern(r"Bio-Sense|Detect Life", meta.handle_detect_life)
        self.register_pattern(r"Pulse|Healing Wave", meta.handle_full_heal)
        self.register_pattern(r"Necrotic|Rotting damage", meta.handle_necrotic)
        self.register_pattern(r"Swarm|Turn into swarm", meta.handle_swarm_form)
        self.register_pattern(r"Contagion|Spread Disease", meta.handle_contagion)
        self.register_pattern(r"Enlarge|Grow Size", meta.handle_enlarge)
        self.register_pattern(r"Appendage|Grow Arm", meta.handle_grow_appendage)
        self.register_pattern(r"Goodberry|Create Food", meta.handle_goodberry)
        self.register_pattern(r"Consume|Eat Ally", meta.handle_consume_ally)
        self.register_pattern(r"Bond|Life Bond", meta.handle_life_bond)
        self.register_pattern(r"Auto-Life|Prevent Death", meta.handle_auto_life)
        self.register_pattern(r"Bane|Bonus vs Creature", meta.handle_creature_bane)
        self.register_pattern(r"Solar|Radiant Beam", meta.handle_laser) # Reusing laser for solar
        self.register_pattern(r"Massive DoT|Heavy Poison", meta.handle_massive_dot)
        self.register_pattern(r"Create Life|Genesis", meta.handle_create_life)
        self.register_pattern(r"Stop Bleed|Clot wound", meta.handle_stop_bleed)
        self.register_pattern(r"Poison|Inflict Poison", meta.handle_venom_injection)

        # --- RATIO SCHOOL ---
        self.register_pattern(r"Confused|Attack Ally|Hit Self", meta.handle_confused) # Ratio 04, 30
        self.register_pattern(r"Psychic damage|Mind Blast", meta.handle_psychic_damage)
        self.register_pattern(r"Mind Control|Charm", meta.handle_charm)
        self.register_pattern(r"Fear|Frighten|Panic", meta.handle_fear)
        self.register_pattern(r"Logic Bomb|Stun Construct", meta.handle_logic_bomb)
        self.register_pattern(r"Rewrite|Edit Physics", meta.handle_rewrite_physics)
        self.register_pattern(r"Delete|Erase Entity", meta.handle_delete_entity)
        self.register_pattern(r"Edit Memory|Modify Memory", meta.handle_edit_memory)
        self.register_pattern(r"Analyze|Identify Weakness", meta.handle_analyze)
        self.register_pattern(r"Calculate|Predict Outcome", meta.handle_calculate)
        self.register_pattern(r"Mind Read|Detect Thoughts", meta.handle_mind_read)
        self.register_pattern(r"Telepathy|Mental Link", meta.handle_empathy_link)
        self.register_pattern(r"Encrypt|Hide Info", meta.handle_encrypt)
        self.register_pattern(r"Illusion|Create Image", meta.handle_illusion)
        self.register_pattern(r"Disguise|Change Appearance", meta.handle_disguise)
        self.register_pattern(r"Invisibility|Turn Invisible", meta.handle_invisibility)
        self.register_pattern(r"Silence|Prevent Casting", meta.handle_silence)
        self.register_pattern(r"Truth|Zone of Truth", meta.handle_prevent_lying)
        self.register_pattern(r"Command|Force Action", meta.handle_force_speech)
        self.register_pattern(r"Sleep|Put to Sleep", meta.handle_stasis) # Reusing stasis logic
        self.register_pattern(r"Dream|Enter Dream", meta.handle_hidden_reality)
        self.register_pattern(r"Nightmare|Psychic Terror", meta.handle_fear)
        self.register_pattern(r"Blind|Remove Sight", meta.handle_blindness)
        self.register_pattern(r"Deaf|Remove Hearing", meta.handle_silence)
        self.register_pattern(r"Haste|Extra Action", meta.handle_double_turn)
        self.register_pattern(r"Slow|Reduce Speed", utility.handle_burden)
        self.register_pattern(r"Hold Person|Paralyze", meta.handle_halt_movement)
        self.register_pattern(r"Feeblemind|Reduce Int", meta.handle_stat_drain)
        self.register_pattern(r"Geas|Quest", meta.handle_oath_bond)
        self.register_pattern(r"Legend Lore|Know History", meta.handle_postcognition)

        # --- AURA SCHOOL ---
        self.register_pattern(r"Light|Create Light|Flash", utility.handle_light)
        self.register_pattern(r"Dazzle|Blind target temporary", utility.handle_dazzle)
        self.register_pattern(r"Blindness|Remove Sight permanent", meta.handle_perm_blind)
        self.register_pattern(r"Reveal|Dispel Invisibility", utility.handle_reveal)
        self.register_pattern(r"Aura of Courage|Immune to Fear", utility.handle_aura_courage)
        self.register_pattern(r"Sanctuary|Prevent Attack", utility.handle_sanctuary)
        self.register_pattern(r"Ward|Share Damage", utility.handle_ward)
        self.register_pattern(r"Shield|AC Bonus", defense.handle_ac_buff)
        self.register_pattern(r"Reflect Ray|Bounce Spell", defense.handle_reflect_ray)
        self.register_pattern(r"Absorb Element|Resistance", defense.handle_resistance)
        self.register_pattern(r"Immunity|Invulnerable to Type", defense.handle_immunity)
        self.register_pattern(r"Calm|Remove Rage", meta.handle_calm_emotions)
        self.register_pattern(r"Beacon|Guide Allies", utility.handle_light) # Re-use light as beacon
        self.register_pattern(r"Flare|Signal", utility.handle_light)
        self.register_pattern(r"Sunlight|Solar damage", meta.handle_laser)
        self.register_pattern(r"Radiance|Holy damage", meta.handle_laser)
        self.register_pattern(r"Glow|Outline target", utility.handle_light)
        self.register_pattern(r"Dim|Reduce Light", utility.handle_light) # Simplified
        self.register_pattern(r"Darkness|Block Light", utility.handle_light) # Simplified toggle?
        self.register_pattern(r"True Sight|See All", meta.handle_omnivision)
        self.register_pattern(r"X-Ray|See through solid", utility.handle_xray)
        self.register_pattern(r"Divine|Godly power", meta.handle_divine_save) # Ordo 39
        self.register_pattern(r"Blessed|Bless", meta.handle_bless)
        self.register_pattern(r"Consecrate|Holy Ground", meta.handle_create_terrain)
        self.register_pattern(r"Safe Haven|Rest Area", utility.handle_rest)
        self.register_pattern(r"Dome|Force Bubble", meta.handle_create_wall)
        self.register_pattern(r"Prism|Split Light", meta.handle_split_beam)
        self.register_pattern(r"Color Spray|Stun visual", utility.handle_dazzle)
        self.register_pattern(r"Hypnotic|Fascinate", meta.handle_charm)

        # --- LEX SCHOOL ---
        self.register_pattern(r"Command|Force Action", meta.handle_force_speech) # Lex 70
        self.register_pattern(r"Geas|Quest", meta.handle_oath_bond)
        self.register_pattern(r"Forbid|Prevent Action", meta.handle_forbid)
        self.register_pattern(r"Truth|Zone of Truth", meta.handle_prevent_lying)
        self.register_pattern(r"Tongues|Speak Language", utility.handle_tongues)
        self.register_pattern(r"Identify|Reveal Properties", utility.handle_identify)
        self.register_pattern(r"True Name|Control Name", meta.handle_true_name)
        self.register_pattern(r"Law|New Rule|Decree", meta.handle_new_law)
        self.register_pattern(r"Oath|Swear Bond", meta.handle_oath_bond)
        self.register_pattern(r"Silence|Quiet", meta.handle_silence)
        self.register_pattern(r"Power Word|Kill Word", meta.handle_divine_save) # Placeholder for PW Kill
        self.register_pattern(r"Symbol|Sigil", meta.handle_trap_logic)
        self.register_pattern(r"Riddle|Confusion", meta.handle_confused)
        self.register_pattern(r"Maze|Trap in Maze", meta.handle_hidden_reality) # Mental Prison
        self.register_pattern(r"Banish|Send Away", movement.handle_teleport)
        self.register_pattern(r"Summon|Call Ally", meta.handle_create_homunculus)
        self.register_pattern(r"Contract|Deal", meta.handle_oath_bond)
        self.register_pattern(r"Judge|Verdict", meta.handle_calculate) # Logic judgment
        self.register_pattern(r"Sentence|Punish", meta.handle_psychic_damage)
        self.register_pattern(r"Pardon|Forgive", meta.handle_calm_emotions)
        self.register_pattern(r"Exile|Banishment", movement.handle_teleport)
        self.register_pattern(r"Sanctify|Holy Word", meta.handle_divine_save)
        self.register_pattern(r"Blasphemy|Unholy Word", meta.handle_necrotic)
        self.register_pattern(r"Dictate|Write Reality", meta.handle_rewrite_physics)
        self.register_pattern(r"Scribe|Scroll", utility.handle_identify)
        self.register_pattern(r"Read Magic|Decipher", utility.handle_identify)
        self.register_pattern(r"Message|Sending", meta.handle_empathy_link)
        self.register_pattern(r"Shout|Thunderous", meta.handle_sonic_damage)
        self.register_pattern(r"Whisper|Secret", meta.handle_mind_read)
        self.register_pattern(r"Bless|Blessing", meta.handle_bless)

# Global Instance
registry = EffectRegistry()

