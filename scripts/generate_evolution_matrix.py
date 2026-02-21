import json

data = {
    "HEAD": {
        "label": "Mental System (Sensory & Social)",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "mind",
        "bases": {
            "Knowledge": "Ears: bonus to acoustic detection, hearing through walls, or sensing frequency.",
            "Logic": "Nose: bonus to tracking, identifying scents, or detecting chemical changes.",
            "Awareness": "Eyes: bonus to night vision, thermal sight, or seeing through illusions.",
            "Intuition": "Nerves: bonus to reaction timing, initiative, or sensing nearby danger.",
            "Charm": "Emotion: bonus to social insight, resisting fear, or sensing intent.",
            "Willpower": "Jaws: bonus to bite strength, grapple hold, or crushing shells."
        },
        "mechanics": {
            "Knowledge": {
                "Might": "Echo-Slam: Can Hear heartbeats to predict melee strikes (+1 Defense).",
                "Reflexes": "Freq-Shift: Hear spellcasting prep; +2 to save vs Magic.",
                "Endurance": "Sub-Sonic: Unaffected by loud noise or Sonic damage.",
                "Finesse": "Pinpoint: Hear invisible heartbeats; no penalty to hit cloaked targets.",
                "Vitality": "Soul-Pitch: Hear the rhythm of life; heal 1 HP when you Hear a kill.",
                "Fortitude": "Steady-Drum: Cannot be Stunned by sensory overload."
            },
            "Logic": {
                "Might": "Heavy-Scent: Detect chemical armor weakpoints; +1 Armor Shred.",
                "Reflexes": "Adren-Snap: Smelling fear grants +5ft movement speed toward targets.",
                "Endurance": "Pure-Breather: Immune to inhaled toxins or gas clouds.",
                "Finesse": "Blood-Trail: Track wounded targets across any distance/terrain.",
                "Vitality": "Pheromone-Regen: Smelling nearby allies heals 1 HP per turn.",
                "Fortitude": "No-Filter: Cannot be blinded/confused by chemical sprays."
            },
            "Awareness": {
                "Might": "Grit-Sight: See through sand/smoke/dust without penalty.",
                "Reflexes": "Flash-Read: +2 to Initiative by seeing muscle twitches.",
                "Endurance": "Wide-Lens: Cannot be Flanked; sight range is 360 degrees.",
                "Finesse": "Thermal-Pierce: Ignore cover bonuses for targets with body heat.",
                "Vitality": "Light-Bloom: Glow in dark; allies get +1 to hit targets near you.",
                "Fortitude": "Star-Stare: Immune to Blindness effects."
            },
            "Intuition": {
                "Might": "Shock-Absorb: Sense impact before it hits; -1 Blunt damage.",
                "Reflexes": "Primal-Twitch: Reaction: Move 5ft when an enemy enters your reach.",
                "Endurance": "Still-Mind: Sense danger in sleep; cannot be Surprised.",
                "Finesse": "Weak-Sense: Sense the 'color' of a target's weak spot; +1 Crit range.",
                "Vitality": "Life-Sync: Sense the health of all nearby creatures precisely.",
                "Fortitude": "Stone-Soul: Ignore the first psychological fear effect each combat."
            },
            "Charm": {
                "Might": "Aura-Crush: Your presence is so heavy it costs enemies 1 extra SP to move near you.",
                "Reflexes": "Blur-Vibe: Look slightly out of focus; -1 to range attacks against you.",
                "Endurance": "Kind-Vibe: Enemies target you last unless you attack them.",
                "Finesse": "Glamour: Your strikes look like gifts; +1 to hit against sentient creatures.",
                "Vitality": "Bloom-Charm: Plants/Animals are friendly by default.",
                "Fortitude": "Solid-Gold: Cannot be intimidated or magically charmed."
            },
            "Willpower": {
                "Might": "Crushing-Hang: Hold onto grappled targets even if you take damage.",
                "Reflexes": "Lock-Jaw: Bite attacks pin targets; they cannot move until they win a Might contest.",
                "Endurance": "Iron-Grip: Hold items/weapons so hard they cannot be disarmed.",
                "Finesse": "Sunder-Snap: Bite attacks have a 10% chance to break enemy weapons.",
                "Vitality": "Eat-Magic: Biting a spellcaster restores 2 Focus.",
                "Fortitude": "Unbreakable: Jaws can bite through iron/stone obstacles."
            }
        }
    },
    "BODY": {
        "label": "Physical Frame",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "body",
        "bases": {
            "Might": "Absorbing: Reduces incoming blunt damage or knockback.",
            "Reflexes": "Agility: Bonus to defense rolls or evasion when moving.",
            "Endurance": "Cardio: Increases max Stamina pool or recovery rate.",
            "Finesse": "Dexterity: Bonus to escaping grapples or avoiding traps.",
            "Vitality": "Regenerative: Regain HP/Meat during rests or at the start of turns.",
            "Fortitude": "Resistant: Bonus to resisting poison, bleed, or environmental heat/cold."
        },
        "mechanics": {
            "Might": {
                "Knowledge": "Neural-Damp: Reduce Psychic/Mental damage by 1.",
                "Logic": "Sync-Plate: Reduce Piercing/Arrow damage by 1.",
                "Awareness": "Vigilant-Guard: Reduce all damage taken while Moving or Dashing.",
                "Intuition": "Primal-Skin: -2 damage taken while below 30% Max HP.",
                "Charm": "Magnet-Pull: Ranged attacks are slightly diverted; -1 Dmg from projectiles.",
                "Willpower": "Zealot-Mass: Reduce damage taken while performing an Action by 2."
            },
            "Reflexes": {
                "Knowledge": "Tactical-Roll: Gain 1 Focus when you successfully Dodge an attack.",
                "Logic": "Calculated-Snap: +2 to Evasion against Area of Effect skills.",
                "Awareness": "Eagle-Step: Reaction: Move 10ft when an arrow is fired at you.",
                "Intuition": "Flow-State: Double Dodge bonus if no enemies are within 5ft.",
                "Charm": "Dancer-Grace: Moving through enemy spaces does not trigger Opportunity Attacks.",
                "Willpower": "Iron-Drive: Ignore movement speed penalties from Heavy Armor."
            },
            "Endurance": {
                "Knowledge": "Brain-Burn: Gain 1 Stamina whenever you cast a spell that costs Focus.",
                "Logic": "Looping-Vents: Regain 2 Stamina at the end of every turn you don't Move.",
                "Awareness": "Watchers-Rest: Regain double HP/Stamina during a Short Rest.",
                "Intuition": "Heart-Pump: When you drop to 0 SP, heal 5 HP (Once per combat).",
                "Charm": "Warm-Leader: Nearby allies (10ft) regain 1 Stamina per turn.",
                "Willpower": "Deep-Lungs: Max Stamina is increased by 5 permanently."
            },
            "Finesse": {
                "Knowledge": "Hack-Grip: Bonus to breaking locks or disabling mechanical traps.",
                "Logic": "Pivot-Point: Escape grapples automatically using 2 SP.",
                "Awareness": "Trap-Sense: Advantage on saves vs floor-based hazards.",
                "Intuition": "Slip-Stream: +2 to Defense against targets that are currently Grappling.",
                "Charm": "Feign-Fall: Falling prone manually costs 0 SP and increases your Evasion.",
                "Willpower": "Root-Hold: You cannot be forcibly moved or knocked Prone."
            },
            "Vitality": {
                "Knowledge": "Mind-Mend: Regain 1 Focus at the start of your turn if you have half HP.",
                "Logic": "Bio-Batch: Every rest allows you to craft 1 free basic Potion.",
                "Awareness": "Cell-Scan: You can see the weakness of any creature you touch.",
                "Intuition": "Blood-Rush: Heal 2 HP every time you land a Critical Hit.",
                "Charm": "Shared-Blood: You can spend your HP to heal an adjacent ally (1:1 ratio).",
                "Willpower": "Undying: If killed, stay alive for 1 extra turn at 1 HP."
            },
            "Fortitude": {
                "Knowledge": "Mental-Void: Immune to Mind-Control or Possession.",
                "Logic": "Anti-Venom: Immune to Poison and Venom damage.",
                "Awareness": "Thermo-Wall: Resistance to both Fire and Cold damage.",
                "Intuition": "Cure-Gland: Bleeding effects on you end after 1 turn automatically.",
                "Charm": "Safe-Scent: You do not attract hostile beasts in the wild.",
                "Willpower": "Inertia: You cannot be slowed below base movement speed."
            }
        }
    },
    "ARMS": {
        "label": "Mental Drive",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "mind",
        "bases": {
            "Knowledge": "Manipulative: Interacting with complex items, lockpicking, or tool use.",
            "Logic": "Tactile: Precise unarmed strikes, disarming enemies, or feeling weak points.",
            "Awareness": "Sensitive: Detecting hidden objects by touch or gaining advantage on aim.",
            "Intuition": "Autonomous: Reflexive parries or automatic counter-attacks.",
            "Charm": "Showy: Distracting flails, imposing presence, or causing target confusion.",
            "Willpower": "Steadfast: Grappling or holding or withstanding force."
        },
        "mechanics": {
            "Knowledge": {
                "Might": "Fast-Load: Reloading ranged weapons costs 1 less SP.",
                "Reflexes": "Quick-Swap: Swapping weapons is a Free Action once per turn.",
                "Endurance": "Heavy-Wrench: Use tools as weapons without penalty (1d6 dmg).",
                "Finesse": "Needle-Point: Use items (potions/bombs) at double range.",
                "Vitality": "Patch-Up: Using a healing item restores 2 extra HP.",
                "Fortitude": "Steady-Hands: You can use items while being Grappled."
            },
            "Logic": {
                "Might": "Bone-Snap: Unarmed strikes have a chance to Disarm targets.",
                "Reflexes": "Pressure-Palm: +2 to hit targets wearing Light or no Armor.",
                "Endurance": "Iron-Fist: Unarmed damage is increased by 1 die step (e.g. 1d4 -> 1d6).",
                "Finesse": "Nerve-Strike: Critical hits with hands disable target's next reaction.",
                "Vitality": "Rebound: Missed unarmed strikes grant +1 to hit on next attack.",
                "Fortitude": "Guard-Clamps: Blocks with unarmed hands provide 1 Armor DB."
            },
            "Awareness": {
                "Might": "Heavy-Vibe: Percussion sensing: sense density of walls by tapping.",
                "Reflexes": "Twitch-Grip: If an enemy misses you, your next strike gets +1 to hit.",
                "Endurance": "Long-Reach: Your melee reach is increased by 5ft.",
                "Finesse": "Focus-Sight: Spend 1 Focus to reveal target HP and Focus.",
                "Vitality": "Sun-Touch: Your hands glow; melee hits deal 1 extra Holy damage.",
                "Fortitude": "Dead-Hand: Your arms are immune to numbness or chill effects."
            },
            "Intuition": {
                "Might": "Crush-Counter: If an enemy hits you, your next strike deals +2 damage.",
                "Reflexes": "Snap-Parry: You can parry ranged projectiles with melee weapons.",
                "Endurance": "Deep-Guard: You gain +1 Defense for every adjacent enemy.",
                "Finesse": "Riposte: Successful Dodges allow an immediate free unarmed strike.",
                "Vitality": "Vamp-Grip: Dealing damage with hands restores 1 Stamina.",
                "Fortitude": "Unmoving: You cannot be disarmed of your primary weapon."
            },
            "Charm": {
                "Might": "Flex: Successful hits Cause Fear in targets with lower Might.",
                "Reflexes": "Jester-Flail: Missing an attack Confuses the enemy for 1 turn.",
                "Endurance": "Bright-Armor: Your shiny arms give attackers disadvantage on the first strike.",
                "Finesse": "Feint-Master: Gain +1 to hit for every consecutive miss.",
                "Vitality": "Beacon-Call: Allies gain +1 to hit targets you are currently Grappling.",
                "Fortitude": "Bold-Pose: Spend 2 SP to Taunt all enemies within 15ft."
            },
            "Willpower": {
                "Might": "Titan-Grip: You can use two-handed weapons with one hand at -2 to hit.",
                "Reflexes": "Haste-Hold: Grappling a target costs 1 SP less.",
                "Endurance": "Endless-Hug: Grappled targets take 1d4 crushing damage every turn.",
                "Finesse": "Sever-Hold: Removing a grapple from you deals 2 damage to the enemy.",
                "Vitality": "Drain-Hold: Regain 1 Focus every turn you maintain a grapple.",
                "Fortitude": "Living-Wall: You provide Total Cover to allies standing behind you."
            }
        }
    },
    "LEGS": {
        "label": "Physical Move",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "body",
        "bases": {
            "Might": "Powerful: Power leaps, stomps, or pushing enemies while moving.",
            "Reflexes": "Wired: Bursts of speed, extra dashes, or moving through enemies.",
            "Endurance": "Sturdy: Marching through difficult terrain without slowing down.",
            "Finesse": "Nimble: Wall-running, climbing, or tight-rope balancing.",
            "Vitality": "Adapted: Swimming, gliding, or moving through water/air.",
            "Fortitude": "Resistant: Rooting in place or ignoring floor hazards."
        },
        "mechanics": {
            "Might": {
                "Knowledge": "Slam-Map: Stomping reveals secret doors/traps within 10ft.",
                "Logic": "Impact-Step: Pushing an enemy into a wall deals 1d6 extra damage.",
                "Awareness": "Air-Drop: Landing from 10ft+ deals 1d4 AoE damage to adjacent enemies.",
                "Intuition": "Brute-Jump: Jump distance is doubled; no check needed.",
                "Charm": "Hero-Land: Landing from a jump Taunts nearby enemies.",
                "Willpower": "Heavy-March: Knock down enemies by simply walking through them."
            },
            "Reflexes": {
                "Knowledge": "Tele-Step: Spend 2 Focus to teleport 15ft instead of moving.",
                "Logic": "Apex-Drive: Moving in a straight line for 20ft makes your next hit a Crit.",
                "Awareness": "Wind-Step: You leave a trail of dust; -1 to range hits against you.",
                "Intuition": "Blur-Dash: You are invisible while moving/dashing.",
                "Charm": "Flash-Kick: Ending a dash near an enemy Dazes them.",
                "Willpower": "Unstoppable: You can dash through walls thin enough to be broken."
            },
            "Endurance": {
                "Knowledge": "Map-Run: You ignore movement penalties for explored map areas.",
                "Logic": "Path-Find: You always know the shortest route to your destination.",
                "Awareness": "Sure-Foot: Ignore the first 10ft of difficult terrain each turn.",
                "Intuition": "Lung-Force: Move speed increases by 10ft when at 100% Stamina.",
                "Charm": "Trek-Leader: Allies following your path move 25% faster out of combat.",
                "Willpower": "Mile-Eater: You never suffer exhaustion from long-distance travel."
            },
            "Finesse": {
                "Knowledge": "Gap-Snap: You can squeeze through spaces half your width.",
                "Logic": "Wall-Logic: Move across walls as if they were floor.",
                "Awareness": "Edge-Hanging: You can hang from ledges and fire one-handed weapons.",
                "Intuition": "Cat-Land: Fall damage is reduced by 50% automatically.",
                "Charm": "Show-Flip: Successful Dodges grant your allies +1 to hit that target.",
                "Willpower": "Sky-Walking: You can walk on water or other liquids for 1 turn."
            },
            "Vitality": {
                "Knowledge": "Aqua-Link: You can breathe underwater and swim at full speed.",
                "Logic": "Air-Current: You can glide 2ft forward for every 1ft you fall.",
                "Awareness": "Deep-Dive: Sense movement in water/air up to 100ft.",
                "Intuition": "Fins-Up: +10ft move speed while in water or rain.",
                "Charm": "Splash-Vibe: Emerging from water Dazes enemies for 1 turn.",
                "Willpower": "True-Adapted: You suffer no penalties from extreme high/low pressure."
            },
            "Fortitude": {
                "Knowledge": "Trap-Shield: Ignore the first floor trap triggered each floor.",
                "Logic": "Heat-Walk: Walk across lava/acid taking only 50% damage.",
                "Awareness": "Grit-Heels: You cannot be moved by wind or repelling spells.",
                "Intuition": "Root-Vibe: Regain 1 HP if you don't move for 2 consecutive turns.",
                "Charm": "Statue-Pose: When standing still, you are indistinguishable from a statue.",
                "Willpower": "Unshakable: You ignore the first 2 squares of knockback from any source."
            }
        }
    },
    "SKIN": {
        "label": "Physical Layer",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "body",
        "bases": {
            "Might": "Hard: Grants natural armor DB or reduces slashing damage.",
            "Reflexes": "Slick: Makes you harder to grapple or causes ranged attacks to slip off.",
            "Endurance": "Fur: Protection against cold or storage of static energy.",
            "Finesse": "Elastic: Bonus to stealth or squeezed movement through gaps.",
            "Vitality": "Fatty: Storage of energy (Focus/Stamina) or protection from hunger.",
            "Fortitude": "Adaptive: Changes color/texture to match the environment (Camo)."
        },
        "mechanics": {
            "Might": {
                "Knowledge": "Data-Pore: Natural Armor (+1 DB) vs Magic projectiles.",
                "Logic": "Cell-Latice: Natural Armor (+1 DB) vs Slashing/Blunt damage.",
                "Awareness": "Glow-Plates: Enemies hit by you are Sparked (Revealed).",
                "Intuition": "Reactive-Hide: First hit taken in combat deals 50% damage.",
                "Charm": "Chrome-Skin: Reflects light; attackers get -1 to hit you.",
                "Willpower": "Spiny-Hide: Enemies hitting you in melee take 1 damage."
            },
            "Reflexes": {
                "Knowledge": "Oil-Mind: +2 bonus to escaping all physical constraints.",
                "Logic": "Slip-Logic: Missed attacks against you cost the enemy 1 SP.",
                "Awareness": "Glass-Skin: Projectiles have a 10% chance to miss automatically.",
                "Intuition": "Water-Body: You take 0 damage from falling into liquids.",
                "Charm": "Shiny-Coat: Attacking you has a chance to Blind the enemy.",
                "Willpower": "True-Slick: You cannot be pinned or restrained by any means."
            },
            "Endurance": {
                "Knowledge": "Static-Charge: Moving 30ft without hitting an enemy shocks the next one (1d6).",
                "Logic": "Fiber-Coat: Total immunity to Cold and Frost damage.",
                "Awareness": "Mood-Fur: Change color based on emotion; +2 Intimidation.",
                "Intuition": "Primal-Mane: Hostile beasts under Level 5 will not attack you.",
                "Charm": "Soft-Touch: Touching an ally heals them for 1 HP (Once per rest).",
                "Willpower": "Iron-Wool: Natural Armor (+1 DB) while at full Stamina."
            },
            "Finesse": {
                "Knowledge": "Code-Camo: +2 to Stealth in electronic or mechanical ruins.",
                "Logic": "Grid-Camo: +2 to Stealth in urban/structured environments.",
                "Awareness": "Night-Camo: +2 to Stealth in Darkness or Dim light.",
                "Intuition": "Shadow-Bound: You can hide in an enemy's shadow (+5 Stealth).",
                "Charm": "Mirror-Skin: You look like whoever is looking at you (-2 to hit).",
                "Willpower": "Silent-Skin: Your movement makes zero noise; ignore sound-based detection."
            },
            "Vitality": {
                "Knowledge": "Data-Store: Can store 1 extra Potion in a skin pouch.",
                "Logic": "Salt-Store: You can go 7 days without water or food.",
                "Awareness": "Warmth-Pore: Nearby allies are protected from extreme Cold.",
                "Intuition": "Hibernator: Long Rests only take 4 hours to complete.",
                "Charm": "Pleasant-Scent: Nearby friends (10ft) get +1 to all social rolls.",
                "Willpower": "Second-Heart: Permanent +2 Max HP."
            },
            "Fortitude": {
                "Knowledge": "Scan-Shelter: You are invisible to magical scanning or radar.",
                "Logic": "Refract-Wall: Projectile magic has a 20% chance to bounce back.",
                "Awareness": "Bio-Mirror: You automatically copy a target's damage resistance for 2 turns.",
                "Intuition": "Earth-Melt: When you are prone on dirt, you gain +10 Stealth.",
                "Charm": "Social-Camo: You blend into crowds perfectly; cannot be singled out.",
                "Willpower": "Deep-Camo: Even creatures with Tremorsense cannot find you."
            }
        }
    },
    "SPECIAL": {
        "label": "Physical Stat",
        "mind_stats": ["Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower"],
        "body_stats": ["Might", "Reflexes", "Endurance", "Finesse", "Vitality", "Fortitude"],
        "mechanic_lead": "body",
        "bases": {
            "Might": "Enviro: hot/cold resistance, gliding, swimming, climbing etc.",
            "Reflexes": "Tool: digging claws, fighting claws, padded paws, etc.",
            "Endurance": "Tank: hoarding pouch, camel humps, etc.",
            "Finesse": "Tail: trip, interact, or hold item well climbing, etc.",
            "Vitality": "Toxic: poison damage (with bite, claws, quills, etc.)",
            "Fortitude": "Horn: horn attack, or parry, cause distraction, etc."
        },
        "mechanics": {
            "Might": {
                "Knowledge": "Brain-Vibe: Send long-range pulses to communicate with allies.",
                "Logic": "Map-Pore: Your skin records the terrain as you walk (Auto-map).",
                "Awareness": "Heat-Flare: Emit a flash of heat; deals 1d4 damage to adj enemies.",
                "Intuition": "Safe-Step: You can sense if a surface is safe to walk on.",
                "Charm": "Glow-Pulse: Emit light in a 30ft radius at will.",
                "Willpower": "Deep-Burn: Spend 1 Focus to emit a beam of fire (1d8)."
            },
            "Reflexes": {
                "Knowledge": "Mod-Grip: You can use any object as a tool for crafting.",
                "Logic": "Wall-Claw: Climb vertical wooden/stone walls at full speed.",
                "Awareness": "Vibe-Feel: Detect trap triggers through your feet.",
                "Intuition": "Bone-Blade: Your natural claws deal +2 damage to unarmored targets.",
                "Charm": "Spark-Claws: Hits with claws have a 5% chance to Stun.",
                "Willpower": "Slayer-Edge: Claws deal 2x damage against Beast types."
            },
            "Endurance": {
                "Knowledge": "Scroll-Gut: You can 'eat' a spell scroll to gain its effect later.",
                "Logic": "Ammo-Pouch: You can store 2x more ammunition than normal.",
                "Awareness": "Liquid-Lung: You can store 1 gallon of water inside your body.",
                "Intuition": "Panic-Sac: When you drop below 5 HP, gain 10 temporary Stamina.",
                "Charm": "Sugar-Store: You can produce 1 piece of food per day.",
                "Willpower": "Mana-Hump: You can store 5 extra Focus points for later use."
            },
            "Finesse": {
                "Knowledge": "Wire-Tail: Use your tail to pick locks remotely (10ft range).",
                "Logic": "Tri-Balance: You cannot be knocked prone while your tail touches the floor.",
                "Awareness": "Blind-Tail: Your tail senses movement behind you; you cannot be Flanked.",
                "Intuition": "Whip-Crack: Action: Your tail attack (1d4) knocks the enemy 5ft back.",
                "Charm": "Tickle-Tail: Tail attack confuses the target for 1 turn.",
                "Willpower": "Crane-Tail: You can hang from your tail and keep both hands free."
            },
            "Vitality": {
                "Knowledge": "Neural-Venom: Poison damage also drains 1 Focus from the target.",
                "Logic": "Quick-Venom: Poison takes effect immediately (No start-of-turn delay).",
                "Awareness": "Neuro-Toxic: Poisoned enemies have -2 to hit you.",
                "Intuition": "Burn-Venom: Poison deals Acid damage instead of Poison damage.",
                "Charm": "Sweet-Venom: Poisoned enemies are also Charmed toward you.",
                "Willpower": "Death-Venom: Poison deals 1d8 damage instead of 1d4."
            },
            "Fortitude": {
                "Knowledge": "Echo-Horn: Bumping horns detects the level of an enemy.",
                "Logic": "Point-Horn: Spend 1 SP to gain +2 to hit with your next melee strike.",
                "Awareness": "Glow-Horn: Your horn lights up when hidden enemies are near (10ft).",
                "Intuition": "Gore-Vibe: Horn attacks deal double damage to bleeding targets.",
                "Charm": "Crown-Horn: Nearby allies get +2 to Resisting Fear.",
                "Willpower": "Spirit-Horn: Your horn can parry magical projectiles."
            }
        }
    }
}

result = {"slots": {}}

for slot_id, slot_data in data.items():
    slot_entry = {
        "label": slot_data["label"],
        "body_stats": slot_data["body_stats"],
        "mind_stats": slot_data["mind_stats"],
        "descriptions": slot_data["bases"],
        "matrix": {}
    }
    
    lead_stats = slot_data["mind_stats"] if slot_data["mechanic_lead"] == "mind" else slot_data["body_stats"]
    qualify_stats = slot_data["body_stats"] if slot_data["mechanic_lead"] == "mind" else slot_data["mind_stats"]
    
    for lead in lead_stats:
        slot_entry["matrix"][lead] = {}
        for qualify in qualify_stats:
            lead_base = slot_data["bases"][lead].split(":")[0]
            
            # The name is still generic/generic in the matrix, 
            # as the Kingdom flavoring will prefix it.
            # But the mechanics are now VERY specific.
            mechanic = slot_data["mechanics"][lead][qualify]
            
            slot_entry["matrix"][lead][qualify] = {
                "name": f"{qualify} {lead_base}",
                "mechanic": mechanic
            }
            
    result["slots"][slot_id] = slot_entry

with open("c:/Users/krazy/Documents/GitHub/TALEWEAVERS/TALEWEAVERS/data/Evolution_Matrix.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4)
