
import pygame
import os
import csv
import json
import random

# --- CONSTANTS ---
COLOR_BG = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (100, 200, 255)
COLOR_BTN = (60, 60, 70)
COLOR_BTN_HOVER = (80, 80, 100)
COLOR_HIGHLIGHT = (255, 200, 50)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../Data")

class DataManager:
    def __init__(self):
        self.species_stats = {}
        self.evolutions = {} 
        self.skills = {} 
        self.backgrounds = {} 
        self.abilities = {} 
        self.gear = []
        
        self.load_all()

    def load_csv(self, filename):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = list(csv.DictReader(f))
                # print(f"[DataManager] Loaded {filename}: {len(data)} rows")
                return data
        except Exception as e:
            print(f"[DataManager] Error loading {filename}: {e}")
            return []

    def load_all(self):
        # 1. Species
        rows = self.load_csv("Species.csv")
        if rows:
            headers = [k for k in rows[0].keys() if k not in ["Attribute", "Reference", ""]]
            for sp in headers:
                self.species_stats[sp] = {}
                for row in rows:
                    attr = row.get("Attribute")
                    val = row.get(sp)
                    try: self.species_stats[sp][attr] = int(val)
                    except: pass
        
        # 2. Evolutions & Skills
        for sp in self.species_stats:
            self.evolutions[sp] = self.load_csv(f"{sp}.csv")
            self.skills[sp] = self.load_csv(f"{sp}_Skills.csv")
            
        # 3. Lists
        self.weapon_groups = self.load_csv("Weapon_Groups.csv")
        self.armor_groups = self.load_csv("Armor_Groups.csv")
        self.social_off = self.load_csv("Social_Off.csv")
        self.social_def = self.load_csv("Social_Def.csv")
        self.utility_skills = [r for r in self.load_csv("Skills.csv") if r.get("Type") == "Utility"]
        self.tool_skills = self.load_csv("Tool_types.csv")
        
        # 4. Powers
        self.spells_t1 = [r for r in self.load_csv("Schools of Power.csv") if str(r.get("Tier")) == "1"]
        self.power_power = [r for r in self.load_csv("Power_Power.csv") if str(r.get("Tier")) == "1"]
        self.power_shapes = [r for r in self.load_csv("Power_Shapes.csv") if str(r.get("Tier")) == "1"]
        self.power_targets = [r for r in self.load_csv("Power_Targets.csv") if str(r.get("Tier")) == "1"] # Speculated file name?
        
        # 5. Gear
        self.all_gear = self.load_csv("weapons_and_armor.csv")

class Dropdown:
    def __init__(self, x, y, w, h, options, placeholder="Select..."):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected = None
        self.placeholder = placeholder
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 14)
        
    def draw(self, screen):
        # Draw Button
        pygame.draw.rect(screen, COLOR_BTN, self.rect)
        pygame.draw.rect(screen, (200,200,200), self.rect, 1)
        
        txt = self.selected if self.selected else self.placeholder
        surf = self.font.render(str(txt)[:25], True, COLOR_TEXT)
        screen.blit(surf, (self.rect.x + 5, self.rect.y + 5))
    
    def draw_list(self, screen):
        if not self.is_open: return
        h = min(len(self.options) * 25, 300)
        
        # Draw Upwards if too close to bottom
        screen_h = screen.get_height()
        if self.rect.y + self.rect.h + h > screen_h:
             list_rect = pygame.Rect(self.rect.x, self.rect.y - h, self.rect.w, h)
        else:
             list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.h, self.rect.w, h)

        pygame.draw.rect(screen, COLOR_PANEL, list_rect)
        pygame.draw.rect(screen, (100,100,100), list_rect, 1)
        
        for i, opt in enumerate(self.options):
            dy = i * 25
            if dy > 275: break
            
            opt_rect = pygame.Rect(list_rect.x, list_rect.y + dy, list_rect.w, 25)
            # Hover check
            mx, my = pygame.mouse.get_pos()
            color = COLOR_BTN_HOVER if opt_rect.collidepoint((mx, my)) else COLOR_PANEL
            pygame.draw.rect(screen, color, opt_rect)
            
            s_txt = self.font.render(str(opt)[:30], True, COLOR_TEXT)
            screen.blit(s_txt, (opt_rect.x + 5, opt_rect.y + 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # print(f"DEBUG: Click at {event.pos} on DD {self.placeholder} (Rect: {self.rect}, Open: {self.is_open})")
                if self.is_open:
                    h = min(len(self.options) * 25, 300)
                    
                    # Logic must match draw_list
                    screen = pygame.display.get_surface()
                    screen_h = screen.get_height() if screen else 700
                    
                    if self.rect.y + self.rect.h + h > screen_h:
                         list_rect = pygame.Rect(self.rect.x, self.rect.y - h, self.rect.w, h)
                    else:
                         list_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.h, self.rect.w, h)

                    if list_rect.collidepoint(event.pos):
                        idx = (event.pos[1] - list_rect.y) // 25
                        if 0 <= idx < len(self.options):
                            self.selected = self.options[idx]
                            self.is_open = False
                            print(f"DEBUG: Selected {self.selected}")
                            return True
                    
                    # Close if clicked outside list AND outside button (toggle logic handles button)
                    if not self.rect.collidepoint(event.pos):
                        self.is_open = False
                        # print("DEBUG: Closed by outside click")
                
                # Button Click (Toggle)
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    return True
        return False


class BuilderUI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Courier New", 16)
        self.data = DataManager()
        
        # State
        self.name = "Hero"
        self.name_focused = False  # Click to edit name
        self.debug_click = ""  # Debug for click detection
        self.points_remaining = 12
        self.stats = {
            "Might": 10, "Reflexes": 10, "Endurance": 10, "Vitality": 10,
            "Fortitude": 10, "Knowledge": 10, "Logic": 10, "Awareness": 10,
            "Intuition": 10, "Charm": 10, "Willpower": 10, "Finesse": 10
        }
        self.allocations = {k:0 for k in self.stats}
        
        # Dropdowns
        self.dd_species = Dropdown(100, 50, 150, 30, list(self.data.species_stats.keys()), "Species")
        
        # Traits (6)
        self.dd_traits = [Dropdown(50 + i*160, 350, 150, 30, [], f"Trait {i+1}") for i in range(6)]
        
        # Skills (7)
        self.dd_skills = {
            "Melee": Dropdown(50, 450, 150, 30, [x['Family Name'] for x in self.data.weapon_groups if x['Type'] == 'Melee'], "Melee Skill"),
            "Ranged": Dropdown(210, 450, 150, 30, [x['Family Name'] for x in self.data.weapon_groups if x['Type'] == 'Ranged'], "Ranged Skill"),
            "Soc Off": Dropdown(370, 450, 150, 30, [x['Skill Name'] for x in self.data.social_off], "Social Off"),
            "Soc Def": Dropdown(530, 450, 150, 30, [x['Skill Name'] for x in self.data.social_def], "Social Def"),
            "Armor": Dropdown(690, 450, 150, 30, [x['Family Name'] for x in self.data.armor_groups], "Armor Skill"),
            "Utility": Dropdown(50, 500, 150, 30, [x['Skill Name'] for x in self.data.utility_skills], "Utility"),
            "Tool": Dropdown(210, 500, 150, 30, [x['Tool_Name'] for x in self.data.tool_skills], "Tool"),
            "Species": Dropdown(370, 500, 200, 30, [], "Species Ability"),
        }
        
        # Spells (2)
        self.dd_spells = [Dropdown(50 + i*250, 600, 240, 30, [], f"Spell {i+1}") for i in range(2)]
        
        # Gear
        self.dd_gear = {
            "Weapon": Dropdown(600, 600, 200, 30, [x['Name'] for x in self.data.all_gear if x.get('Type') == 'Weapon'], "Weapon"),
            "Armor": Dropdown(810, 600, 200, 30, [x['Name'] for x in self.data.all_gear if x.get('Type') == 'Armor'], "Armor"),
        }
        
    def update_stats(self):
        # Reset to base
        sp = self.dd_species.selected
        if not sp: return
        
        base = self.data.species_stats.get(sp, {})
        for k in self.stats:
            self.stats[k] = base.get(k, 10) + self.allocations[k]
            
        # Update Trait Options based on Species
        cats = ["ANCESTRY", "DEFENSE", "OFFENSE", "SOCIAL", "ENVIRON", "ADAPT"]
        sp_traits = self.data.evolutions.get(sp, [])
        
        for i, dd in enumerate(self.dd_traits):
            if i < len(cats):
                # Filter to Unique Body Parts
                cat_rows = [r for r in sp_traits if r["Category"] == cats[i]]
                body_parts = []
                seen = set()
                for r in cat_rows:
                    bp = r.get("Body Part")
                    if bp and bp not in seen:
                        body_parts.append(bp)
                        seen.add(bp)
                
                dd.options = body_parts
                if dd.selected not in body_parts: dd.selected = None

        # Update Species Ability Options
        selected_parts = []
        for dd in self.dd_traits:
            if dd.selected:
                selected_parts.append(dd.selected)
        
        sp_skills = self.data.skills.get(sp, [])
        valid_sp = []
        for s in sp_skills:
             # Match based on selected Body Part directly
             req = s.get("Body Part") or s.get("Required Body Part")
             if req in selected_parts:
                 valid_sp.append(s.get("Skill Name") or s.get("Skill"))
        
        self.dd_skills["Species"].options = valid_sp

        # Update Spells (Stat >= 12)
        valid_spells = []
        for r in self.data.spells_t1:
            attr = r.get("Attribute")
            if self.stats.get(attr, 0) >= 12:
                valid_spells.append(f"{r['Name']} ({attr})")
        for dd in self.dd_spells:
            dd.options = valid_spells

        # Update Weapon Gear based on User Skills
        # Map Weapon_Groups Name -> weapons_and_armor Related_Skill
        fam_map = {
             "Large Weapons": "Great",
             "Medium Weapons": "Medium", 
             "Small Weapons": "Small", 
             "Fist Weapons": "Fist",
             "Reach Weapons": "Large",
             "Exotic Weapons": "Exotic Melee",
             "Ballistic Weapons": "Ballistics",
             # Others usually match (Thrown, Simple, Blast, Long Shot)
        }
        
        # Collect selected families
        sel_fams = []
        if self.dd_skills["Melee"].selected: sel_fams.append(self.dd_skills["Melee"].selected)
        if self.dd_skills["Ranged"].selected: sel_fams.append(self.dd_skills["Ranged"].selected)
        
        # Translate to Gear Skills
        valid_gear_skills = [fam_map.get(f, f) for f in sel_fams]
        
        # Filter Gear
        w_opts = [g['Name'] for g in self.data.all_gear 
                  if g.get('Type') == 'Weapon' and g.get('Related_Skill') in valid_gear_skills]
        
        print(f"DEBUG WEAPONS: Selected Fams={sel_fams}, Mapped Skills={valid_gear_skills}, Weapon Options={w_opts}")
        
        self.dd_gear["Weapon"].options = w_opts


        # Update Armor Gear based on Skill (using new canonical names)
        armor_skill = self.dd_skills["Armor"].selected
        if armor_skill:
            req_skill = armor_skill.strip()
            # Armor skills are now: Cloth, Light, Medium, Heavy, Natural, Utility
            opts = [g['Name'] for g in self.data.all_gear 
                    if g.get('Type') == 'Armor' and g.get('Related_Skill') == req_skill]
            self.dd_gear["Armor"].options = opts
        else:
            self.dd_gear["Armor"].options = []


    def draw(self):
        self.screen.fill(COLOR_BG)
        # Name Input Box
        name_rect = pygame.Rect(50, 15, 200, 30)
        box_color = (100, 150, 200) if self.name_focused else COLOR_BTN
        pygame.draw.rect(self.screen, box_color, name_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), name_rect, 2)
        
        # Add blinking cursor if focused
        cursor = "|" if self.name_focused and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        nm_surf = self.font.render(f"{self.name}{cursor}", True, COLOR_TEXT)
        self.screen.blit(nm_surf, (55, 20))
        
        # Debug click display
        if self.debug_click:
            dbg = self.font.render(self.debug_click, True, (255, 255, 0))
            self.screen.blit(dbg, (300, 20))
        
        # Species
        self.dd_species.draw(self.screen)
        
        # Stats
        y = 100
        x = 50
        pts_surf = self.font.render(f"Pool: {self.points_remaining}", True, COLOR_HIGHLIGHT)
        self.screen.blit(pts_surf, (50, 80))
        
        for k, v in self.stats.items():
            s_str = f"{k}: {v}"
            self.screen.blit(self.font.render(s_str, True, COLOR_TEXT), (x, y))
            
            # Buttons [-] [+]
            pygame.draw.rect(self.screen, (100,50,50), (x+160, y, 20, 20)) # -
            pygame.draw.rect(self.screen, (50,100,50), (x+185, y, 20, 20)) # +
            
            if x > 600: 
                x = 50; y += 30
            else:
                x += 300
        
        # Traits
        for dd in self.dd_traits: dd.draw(self.screen)
            
        # Skills
        for k, dd in self.dd_skills.items():
            self.screen.blit(self.font.render(k, True,(150,150,150)), (dd.rect.x, dd.rect.y-15))
            dd.draw(self.screen)
            
        # Spells
        for i, dd in enumerate(self.dd_spells): dd.draw(self.screen)
        
        # Gear
        for k, dd in self.dd_gear.items(): dd.draw(self.screen)

        # Bottom Buttons
        btn_y = 640 
        
        pygame.draw.rect(self.screen, (100, 50, 50), (50, btn_y, 150, 50))
        self.screen.blit(self.font.render("CANCEL", True, (255,255,255)), (80, btn_y+15))

        rgb = (50, 200, 50) if self.points_remaining == 0 else (100,100,100)
        pygame.draw.rect(self.screen, rgb, (750, btn_y, 200, 50))
        self.screen.blit(self.font.render("SAVE & SPAWN", True, (0,0,0)), (770, btn_y+15))
        
        # RANDOM Button
        pygame.draw.rect(self.screen, (100, 100, 200), (220, btn_y, 120, 50))
        self.screen.blit(self.font.render("RANDOM", True, (255,255,255)), (240, btn_y+15))

        # OVERLAY: Draw Active Dropdown List Last
        all_dds = [self.dd_species] + self.dd_traits + list(self.dd_skills.values()) + self.dd_spells + list(self.dd_gear.values())
        for dd in all_dds:
            if dd.is_open:
                dd.draw_list(self.screen)
                break 

    def handle_event(self, event):
        # PRIORITY: Bottom buttons FIRST (before dropdowns can consume)
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            # SPAWN (750-950, 640-690)
            if 750 <= x <= 950 and 640 <= y <= 690:
                return self.finalize()
            # CANCEL (50-200, 640-690)
            if 50 <= x <= 200 and 640 <= y <= 690:
                return {"CANCEL": True}
            # RANDOM (220-340, 640-690)
            if 220 <= x <= 340 and 640 <= y <= 690:
                self.debug_click = "RANDOM CLICKED!"
                try:
                    self.randomize()
                except Exception as e:
                    self.debug_click = f"ERROR: {e}"
                return  # Consume the event
            else:
                self.debug_click = f"Click at ({x}, {y})"
        
        # 1. Dropdowns (Z-Order Priority)
        all_dds = [self.dd_species] + self.dd_traits + list(self.dd_skills.values()) + self.dd_spells + list(self.dd_gear.values())
        
        # Prioritize Open DD (ONLY for mouse clicks)
        open_dd = next((dd for dd in all_dds if dd.is_open), None)
        if open_dd and event.type == pygame.MOUSEBUTTONDOWN:
            if open_dd.handle_event(event):
                if open_dd == self.dd_species:
                    self.allocations = {k:0 for k in self.stats}
                    self.points_remaining = 12
                    self.update_stats()
                else:
                    self.update_stats()
                return 
        
        # Check others if not consumed (ONLY for mouse clicks)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for dd in all_dds:
                if dd is not open_dd and dd.handle_event(event):
                    if dd == self.dd_species:
                        self.allocations = {k:0 for k in self.stats}
                        self.points_remaining = 12
                        self.update_stats()
                    else:
                        self.update_stats()
                    # Close others
                    for other in all_dds:
                        if other != dd: other.is_open = False
                    return 

        # 2. Click Handling (Buttons)
        if event.type == pygame.MOUSEBUTTONDOWN:
            # SPAWN
            if 750 <= event.pos[0] <= 950 and 640 <= event.pos[1] <= 690:
                 return self.finalize()

            # CANCEL
            if 50 <= event.pos[0] <= 200 and 640 <= event.pos[1] <= 690:
                return {"CANCEL": True}

            # RANDOM
            if 220 <= event.pos[0] <= 340 and 640 <= event.pos[1] <= 690:
                print("DEBUG: RANDOM button clicked!")
                try:
                    self.randomize()
                except Exception as e:
                    print(f"ERROR in randomize: {e}")

            # Name Input Click (toggle focus)
            name_rect = pygame.Rect(50, 15, 200, 30)
            if name_rect.collidepoint(event.pos):
                self.name_focused = True
            else:
                self.name_focused = False

            # 3. Stat Buttons
            y = 100; x = 50
            for k in self.stats:
                # [-]
                if pygame.Rect(x+160, y, 20, 20).collidepoint(event.pos):
                    if self.allocations[k] > -2: 
                        self.allocations[k] -= 1
                        self.points_remaining += 1
                        self.update_stats()
                # [+]
                if pygame.Rect(x+185, y, 20, 20).collidepoint(event.pos):
                     if self.points_remaining > 0 and self.stats[k] < 18:
                         self.allocations[k] += 1
                         self.points_remaining -= 1
                         self.update_stats()
                
                if x > 600: x = 50; y += 30
                else: x += 300
        
        # Name Input (only when focused)
        if event.type == pygame.KEYDOWN and self.name_focused:
            if event.key == pygame.K_BACKSPACE: self.name = self.name[:-1]
            elif event.key == pygame.K_RETURN: 
                self.name_focused = False
            elif event.unicode and event.unicode.isprintable(): self.name += event.unicode

    def randomize(self):
        """Auto-fill all dropdowns with random valid selections."""
        # 1. Random Species
        if self.dd_species.options:
            self.dd_species.selected = random.choice(self.dd_species.options)
        
        # Reset and update stats first
        self.allocations = {k: 0 for k in self.stats}
        self.points_remaining = 12
        self.update_stats()
        
        # 2. Random Traits
        for dd in self.dd_traits:
            if dd.options:
                dd.selected = random.choice(dd.options)
        self.update_stats()  # Update skills based on traits
        
        # 3. Random Skills
        for dd in self.dd_skills.values():
            if dd.options:
                dd.selected = random.choice(dd.options)
        self.update_stats()  # Update gear based on skills
        
        # 4. Random Spells
        for dd in self.dd_spells:
            if dd.options:
                dd.selected = random.choice(dd.options)
        
        # 5. Random Gear
        for dd in self.dd_gear.values():
            if dd.options:
                dd.selected = random.choice(dd.options)
        
        # 6. Random Stat Allocation (spend all 12 points)
        stat_keys = list(self.stats.keys())
        while self.points_remaining > 0:
            k = random.choice(stat_keys)
            if self.stats[k] < 18:
                self.allocations[k] += 1
                self.points_remaining -= 1
                self.update_stats()
        
        # 7. Random Name
        names = ["Grim", "Valor", "Shadow", "Thunder", "Blaze", "Storm", "Frost", "Iron", "Steel", "Raven"]
        self.name = random.choice(names)
            
    def finalize(self):
        skills = []
        for dd in self.dd_skills.values():
            if dd.selected: skills.append(dd.selected.split(" (")[0]) 
            
        traits = [dd.selected for dd in self.dd_traits if dd.selected]
        powers = [dd.selected.split(" (")[0] for dd in self.dd_spells if dd.selected]
        
        data = {
            "Name": self.name,
            "Species": self.dd_species.selected,
            "Stats": self.stats.copy(),
            "Traits": traits,
            "Skills": skills,
            "Powers": powers,
            "Inventory": [
                self.dd_gear["Weapon"].selected,
                self.dd_gear["Armor"].selected
            ]
        }
        return data
        self.screen.blit(nm_surf, (50, 20))
        
        # Species
        self.dd_species.draw(self.screen)
        
        # Stats
        y = 100
        x = 50
        pts_surf = self.font.render(f"Pool: {self.points_remaining}", True, COLOR_HIGHLIGHT)
        self.screen.blit(pts_surf, (50, 80))
        
        for k, v in self.stats.items():
            s_str = f"{k}: {v}"
            self.screen.blit(self.font.render(s_str, True, COLOR_TEXT), (x, y))
            
            # Buttons [-] [+]
            pygame.draw.rect(self.screen, (100,50,50), (x+160, y, 20, 20)) # -
            pygame.draw.rect(self.screen, (50,100,50), (x+185, y, 20, 20)) # +
            
            if x > 600: 
                x = 50; y += 30
            else:
                x += 300
        
        # Traits
        for dd in self.dd_traits: dd.draw(self.screen)
            
        # Skills
        for k, dd in self.dd_skills.items():
            self.screen.blit(self.font.render(k, True,(150,150,150)), (dd.rect.x, dd.rect.y-15))
            dd.draw(self.screen)
            
        # Spells
        for i, dd in enumerate(self.dd_spells): dd.draw(self.screen)
        
        # Gear
        for k, dd in self.dd_gear.items(): dd.draw(self.screen)

        # Bottom Buttons
        btn_y = 640 
        
        pygame.draw.rect(self.screen, (100, 50, 50), (50, btn_y, 150, 50))
        self.screen.blit(self.font.render("CANCEL", True, (255,255,255)), (80, btn_y+15))

        rgb = (50, 200, 50) if self.points_remaining == 0 else (100,100,100)
        pygame.draw.rect(self.screen, rgb, (750, btn_y, 200, 50))
        self.screen.blit(self.font.render("SAVE & SPAWN", True, (0,0,0)), (770, btn_y+15))
        
        # OVERLAY: Draw Active Dropdown List Last
        all_dds = [self.dd_species] + self.dd_traits + list(self.dd_skills.values()) + self.dd_spells + list(self.dd_gear.values())
        for dd in all_dds:
            if dd.is_open:
                dd.draw_list(self.screen)
                break # Only one open at a time usually
