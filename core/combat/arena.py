import sys
import os

# Add parent path (Project Root) BEFORE importing mechanics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pygame
import mechanics
import enemy_spawner
import time # Input delay for AI visibility
import json

# Add parent path for AI module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
# AI is now handled internally by Mechanics


# Constants
SCREEN_W, SCREEN_H = 1000, 700
TILE_SIZE = 50
GRID_COLS, GRID_ROWS = 12, 12
OFFSET_X, OFFSET_Y = 50, 50

COLOR_BG = (20, 20, 30)
COLOR_GRID = (60, 60, 70)
COLOR_TILE_HOVER = (80, 80, 100)
COLOR_P1 = (100, 200, 100) # Player/Empire
COLOR_P2 = (200, 100, 100) # Enemy/Rebels
COLOR_NEUTRAL = (200, 200, 200)
COLOR_WALL = (100, 100, 100)
COLOR_TURN = (255, 255, 100)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR = os.path.join(BASE_DIR, "../Saves")

class Button:
    def __init__(self, rect, text, callback, args=None, active=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.args = args or []
        self.hover = False
        self.active = active

    def draw(self, screen, font):
        if not self.active: return
        col = (80, 80, 100) if self.hover else (60, 60, 80)
        pygame.draw.rect(screen, col, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        surf = font.render(self.text, True, (220, 220, 220))
        rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, rect)

    def check_click(self, pos):
        if self.active and self.rect.collidepoint(pos):
            self.callback(*self.args)

import builder_ui

class ArenaApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Tactical Combat Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 14)
        self.header_font = pygame.font.SysFont("Courier New", 20, bold=True)
        
        self.state = "SELECT"
        self.buttons = []
        self.engine = mechanics.CombatEngine(GRID_COLS, GRID_ROWS)
        self.fighter1 = None
        self.fighter2 = None
        self.selected_tile = None
        self.log_lines = []
        self.pending_ability = None
        
        # Builder
        self.builder_ui = builder_ui.BuilderUI(self.screen)
        self.active_slot = 1
        
        # Sidebar HUD State
        self.show_actions_menu = False
        self.context_menu = None
        
        # Enemy Spawner
        self.ai_templates = enemy_spawner.get_ai_templates()
        self.selected_ai_template = self.ai_templates[0] if self.ai_templates else "Aggressive"
        self.ai = None

    def start_builder(self, slot):
        self.state = "BUILDER"
        self.active_slot = slot
        self.buttons = []

    def start_loader(self, slot):
        self.state = "LOADER"
        self.active_slot = slot
        self.scan_saves()

    def cancel_load(self):
        self.state = "SELECT"
        self.scan_saves()

    def scan_saves(self):
        self.buttons = []
        if self.state == "SELECT":
            # Slot 1
            lbl1 = f"P1: {self.fighter1.name}" if self.fighter1 else "P1: Empty"
            self.buttons.append(Button((50, 100, 300, 50), lbl1, lambda: None))
            self.buttons.append(Button((360, 100, 100, 50), "BUILD", self.start_builder, [1]))
            self.buttons.append(Button((470, 100, 100, 50), "LOAD", self.start_loader, [1]))
            
            # Slot 2
            lbl2 = f"P2: {self.fighter2.name}" if self.fighter2 else "P2: Empty"
            self.buttons.append(Button((50, 200, 300, 50), lbl2, lambda: None))
            self.buttons.append(Button((360, 200, 100, 50), "BUILD", self.start_builder, [2]))
            self.buttons.append(Button((470, 200, 100, 50), "LOAD", self.start_loader, [2]))
            
            # AI & Spawn
            self.buttons.append(Button((50, 300, 200, 40), f"AI: {self.selected_ai_template}", self.cycle_ai_template))
            self.buttons.append(Button((270, 300, 200, 40), "Auto-Spawn Enemy (P2)", self.spawn_enemy))

            # Start
            if self.fighter1 and self.fighter2:
                self.buttons.append(Button((50, 400, 420, 60), "START COMBAT", self.start_combat))
        
        elif self.state == "LOADER":
            if not os.path.exists(SAVES_DIR): os.makedirs(SAVES_DIR)
            files = [f for f in os.listdir(SAVES_DIR) if f.endswith(".json")]
            self.buttons.append(Button((50, 50, 100, 40), "< CANCEL", self.cancel_load))
            
            y = 100
            for f in files:
                 path = os.path.join(SAVES_DIR, f)
                 self.buttons.append(Button((50, y, 400, 40), f, self.select_fighter, [self.active_slot, path]))
                 y += 50

        elif self.state == "COMBAT":
            base_y = 200
            self.buttons.append(Button((710, base_y, 120, 40), "SHEET", self.open_sheet))
            self.buttons.append(Button((850, base_y, 120, 40), "INVENTORY", self.open_inventory))
            self.buttons.append(Button((710, base_y + 50, 260, 40), "ACTIONS >", self.toggle_actions_menu))
            
            if self.show_actions_menu:
                 active_char = self.engine.get_active_char()
                 skill_y = base_y + 100
                 if active_char:
                     all_abilities = list(active_char.powers) + list(active_char.traits)
                     for ab in all_abilities:
                         self.buttons.append(Button((710, skill_y, 260, 30), ab, self.activate_power_click, [active_char, ab]))
                         skill_y += 35
            
            self.buttons.append(Button((710, 600, 200, 50), "END TURN", self.end_turn))
            
            # AI Toggle Buttons
            p1_ai_txt = "P1 AI: ON" if (self.fighter1 and self.fighter1.data.get("AI")) else "P1 AI: OFF"
            p2_ai_txt = "P2 AI: ON" if (self.fighter2 and self.fighter2.data.get("AI")) else "P2 AI: OFF"
            self.buttons.append(Button((710, 660, 120, 35), p1_ai_txt, self.toggle_p1_ai))
            self.buttons.append(Button((850, 660, 120, 35), p2_ai_txt, self.toggle_p2_ai))
            
            if self.engine.clash_active:
                 self.buttons = []
                 self.buttons.append(Button((SCREEN_W//2 - 150, SCREEN_H//2, 100, 50), "PRESS", self.resolve_clash, ["PRESS"]))
                 self.buttons.append(Button((SCREEN_W//2 + 50, SCREEN_H//2, 100, 50), "DEFEND", self.resolve_clash, ["DEFEND"]))

    def run(self):
        self.scan_saves()
        while True:
            # Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Builder Handling
                if self.state == "BUILDER":
                    res = self.builder_ui.handle_event(event)
                    if res:
                        try:
                            if res.get("CANCEL"):
                                self.state = "SELECT"
                                self.scan_saves()
                            else:
                                # Save Character
                                fname = f"{res.get('Name', 'Unknown')}.json"
                                if not os.path.exists(SAVES_DIR): os.makedirs(SAVES_DIR)
                                fpath = os.path.join(SAVES_DIR, fname)
                                with open(fpath, 'w') as f:
                                    json.dump(res, f, indent=4)
                                print(f"Saved character to {fpath}")
                                
                                # Load into Slot
                                c = mechanics.Combatant(data=res)
                                if self.active_slot == 1: self.fighter1 = c
                                else: self.fighter2 = c
                                self.state = "SELECT"
                                self.scan_saves()
                        except Exception as e:
                            print(f"[Arena] Error saving/loading builder character: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Normal Handling
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Context Menu
                        if self.context_menu and self.context_menu.active:
                            self.context_menu.handle_click(event.pos)
                            continue
                            
                        # Standard Buttons
                        for b in self.buttons:
                            if b.rect.collidepoint(event.pos):
                                b.callback(*b.args)
                                break
                                
                        # Grid Clicks
                        if self.state == "COMBAT":
                             # Convert mouse to grid
                             mx, my = event.pos
                             gx = (mx - OFFSET_X) // TILE_SIZE
                             gy = (my - OFFSET_Y) // TILE_SIZE
                             
                             if 0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS:
                                 self.handle_grid_click(gx, gy)
                             else:
                                 # Click off grid clears selection?
                                 pass

            # Update
            self.update()
            
            # Draw
            self.draw(self.screen, self.font)
            pygame.display.flip()
            self.clock.tick(30)
    
    def update(self):
        # 1. Clash Handling for AI
        if self.state == "COMBAT" and self.engine.clash_active:
             active = self.engine.get_active_char()
             if active and active.data.get("AI"):
                 # AI Auto-Resolve
                 current_time = pygame.time.get_ticks()
                 if not hasattr(self, 'clash_cooldown'): self.clash_cooldown = 0
                 
                 if current_time > self.clash_cooldown:
                     print("AI resolving Clash...")
                     self.resolve_clash("PRESS")
                     self.clash_cooldown = current_time + 1000
             return

        # 2. Normal Turn Loop
        if self.state == "COMBAT" and not self.engine.clash_active:
             # Check if active char is AI
             active = self.engine.get_active_char()
             
             if active and active.data.get("AI"):
                 # AI Turn Logic
                 # We need a timer or state to prevent instant execution every frame
                 current_time = pygame.time.get_ticks()
                 if not hasattr(self, 'ai_cooldown'): self.ai_cooldown = 0
                 
                 # print(f"DEBUG: Time={current_time}, CD={self.ai_cooldown}")
                 
                 if current_time > self.ai_cooldown:
                     print(f"Executing AI Turn for {active.name}...")
                     # Execute Turn
                     try:
                         # 1. Execute Logic
                         ai_log = self.engine.execute_ai_turn(active)
                         print(f"AI LOG: {ai_log}")
                         self.log_lines.extend(ai_log)
                         
                         # 2. End Turn
                         res = self.engine.end_turn()
                         self.log_lines.extend(res)
                         self.scan_saves()
                         
                         # 3. Set Cooldown (e.g. 1000ms)
                         self.ai_cooldown = current_time + 1000
                     except Exception as e:
                         print(f"AI Error: {e}")
                         self.ai_cooldown = current_time + 2000 # Retry slower


    def toggle_actions_menu(self):
        self.show_actions_menu = not self.show_actions_menu
        self.scan_saves()

    def activate_power_click(self, char, power_name):
         # Enter Targeting Mode
         # We could check if ability is "Self" only, but for now let's allow targeting for everything
         # or heuristic check based on "Attack" vs "Heal".
         # Simplest: Enter TARGETING mode, prompt "Select Target".
         self.state = "TARGETING"
         self.pending_ability = (char, power_name)
         self.log_lines.append(f"Select Target for {power_name}...")

    def activate_power_execute(self, target):
         char, power_name = self.pending_ability
         res = self.engine.activate_ability(char, power_name, target)
         self.log_lines.extend(res)
         self.state = "COMBAT"
         self.pending_ability = None
         self.scan_saves()

    def select_fighter(self, slot, path):
        c = mechanics.Combatant(path)
        if slot == 1: self.fighter1 = c
        else: self.fighter2 = c
        self.scan_saves()

    def cycle_ai_template(self):
        idx = self.ai_templates.index(self.selected_ai_template)
        self.selected_ai_template = self.ai_templates[(idx + 1) % len(self.ai_templates)]
        self.scan_saves()

    def spawn_enemy(self):
        data = enemy_spawner.spawner.generate(self.selected_ai_template)
        c = mechanics.Combatant(data=data)
        self.fighter2 = c
        self.log_lines.append(f"Spawned: {c.name} (AI: {self.selected_ai_template})")
        self.scan_saves()

    def start_auto_combat(self):
        if self.fighter1:
            self.fighter1.data["AI"] = "Aggressive"
        self.start_combat()

    def start_combat(self):
        self.engine = mechanics.CombatEngine()
        
        # Assign Teams to ensure hostility
        self.fighter1.team = "Player"
        self.fighter2.team = "Enemy"
        
        # Initial positions
        self.engine.add_combatant(self.fighter1, 3, 3)
        self.engine.add_combatant(self.fighter2, 8, 8)

        
        self.log_lines = self.engine.start_combat()
        self.state = "COMBAT"
        self.scan_saves()

    def reset(self):
        self.fighter1 = None; self.fighter2 = None
        self.state = "SELECT"
        self.engine = mechanics.CombatEngine()
        self.scan_saves()

    def end_turn(self):
        if self.engine.clash_active: return
        res = self.engine.end_turn()
        self.log_lines.extend(res)
        self.scan_saves() # Refresh buttons
        
        self.scan_saves() # Refresh buttons
        # Legacy AI Loop Removed (Handled in Update)

    def resolve_clash(self, choice):
        res = self.engine.resolve_clash(choice)
        self.log_lines.extend(res)
        self.scan_saves()

    def handle_grid_click(self, gx, gy):
        if self.state == "TARGETING":
            # Find target
            target = None
            for c in self.engine.combatants:
                 if c.is_alive() and c.x == gx and c.y == gy:
                     target = c; break
            if target:
                self.activate_power_execute(target)
            else:
                self.log_lines.append("Invalid Target! Click a unit.")
            return

        if self.state != "COMBAT": return
        if self.engine.clash_active: return
        
        actor = self.engine.get_active_char()
        if not actor: return

        # Check if clicked on enemy -> Attack
        target = None
        for c in self.engine.combatants:
            if c.is_alive() and c.x == gx and c.y == gy:
                target = c
                break
        
        if target:
            if target == actor: return # self click
            res = self.engine.attack_target(actor, target)
            self.log_lines.extend(res)
            self.scan_saves() # update if clash
        else:
            # Move
            success, msg = self.engine.move_char(actor, gx, gy)
            self.log_lines.append(msg)
            self.scan_saves() # Refresh buttons for movement update if needed

    def handle_input(self):
        mx, my = pygame.mouse.get_pos()
        # Map Grid Selection
        gx = (mx - OFFSET_X) // TILE_SIZE
        gy = (my - OFFSET_Y) // TILE_SIZE
        self.selected_tile = (gx, gy) if 0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEMOTION:
                for b in self.buttons: b.hover = b.rect.collidepoint((mx, my))
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 1. Handle Context Menu Click
                if self.context_menu and event.button == 1:
                    # Check if clicked option
                    opts = self.context_menu["options"]
                    cx, cy = self.context_menu["pos"]
                    clicked_opt = False
                    for i, (label, cb, args) in enumerate(opts):
                        rect = pygame.Rect(cx, cy + i*30, 150, 30)
                        if rect.collidepoint((mx, my)):
                            if cb: cb(*args)
                            clicked_opt = True
                            break
                    self.context_menu = None # Close on any click
                    if clicked_opt: return # Handled
                elif self.context_menu:
                     self.context_menu = None # Close if clicking outside
                
                # 2. Setup Context Menu (Right Click)
                if event.button == 3:
                     if self.state == "TARGETING":
                         self.state = "COMBAT"
                         self.log_lines.append("Targeting Cancelled.")
                     elif self.state == "COMBAT" and self.selected_tile:
                         self.open_context_menu(gx, gy, (mx, my))
                     return

                if event.button == 1:
                    # UI Buttons
                    clicked_btn = False
                    for b in self.buttons:
                        if b.rect.collidepoint((mx, my)):
                            b.check_click((mx, my))
                            clicked_btn = True
                            break
                    # Map Click
                    if not clicked_btn and self.selected_tile and self.state == "COMBAT":
                        self.handle_grid_click(*self.selected_tile)

    def open_context_menu(self, gx, gy, screen_pos):
        options = []
        target = None
        for c in self.engine.combatants:
            if c.is_alive() and c.x == gx and c.y == gy:
                target = c; break
        
        active = self.engine.get_active_char()
        
        if target:
            options.append(("Inspect", self.open_sheet_target, [target]))
            if active and target != active:
                options.append(("Attack", self.engine_action_wrapper, ["attack", active, target]))
        else:
             if active:
                 options.append(("Move Here", self.engine_action_wrapper, ["move", active, gx, gy]))
        
        if options:
            self.context_menu = {"pos": screen_pos, "options": options}

    def open_sheet_target(self, target):
        self.sheet_target = target
        self.state = "SHEET"
        self.buttons = [Button((SCREEN_W-150, 10, 100, 40), "BACK", self.close_sheet)]

    def engine_action_wrapper(self, action_type, *args):
        if action_type == "move":
            actor, gx, gy = args
            _, msg = self.engine.move_char(actor, gx, gy)
            self.log_lines.append(msg)
        elif action_type == "attack":
            actor, target = args
            res = self.engine.attack_target(actor, target)
            self.log_lines.extend(res)
        self.scan_saves()


    def draw(self, screen, font):
        self.screen.fill(COLOR_BG)
        
        if self.state == "BUILDER":
            self.builder_ui.draw()
            return
        
        if self.state == "INVENTORY":
            self.draw_inventory_screen()
            for b in self.buttons: b.draw(self.screen, self.font)
            pygame.display.flip()
            return
        
        if self.state == "COMBAT":
            # 1. Draw Grid & Terrain
            # Border
            map_rect = (OFFSET_X-5, OFFSET_Y-5, GRID_COLS*TILE_SIZE+10, GRID_ROWS*TILE_SIZE+10)
            pygame.draw.rect(self.screen, COLOR_WALL, map_rect, 5)

            for y in range(GRID_ROWS):
                for x in range(GRID_COLS):
                    rect = (OFFSET_X + x*TILE_SIZE, OFFSET_Y + y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    
                    # WALL CHECK
                    if (x,y) in self.engine.walls:
                        pygame.draw.rect(self.screen, COLOR_WALL, rect)
                    
                    col = COLOR_GRID
                    if self.selected_tile == (x,y) and not self.engine.clash_active:
                        col = COLOR_TILE_HOVER
                    pygame.draw.rect(self.screen, col, rect, 1)

            # 2. Draw Combatants
            for c in self.engine.combatants:
                if not c.is_alive(): continue
                cx = OFFSET_X + c.x * TILE_SIZE
                cy = OFFSET_Y + c.y * TILE_SIZE
                
                # Active Highlight
                if c == self.engine.get_active_char():
                    pygame.draw.rect(self.screen, COLOR_TURN, (cx+2, cy+2, TILE_SIZE-4, TILE_SIZE-4), 2)
                    
                # Team Color
                col = COLOR_P1
                if getattr(c, "team", "") in ["Enemy", "Rebels"]:
                    col = COLOR_P2
                elif getattr(c, "team", "") == "Neutral":
                    col = COLOR_NEUTRAL
                elif c != self.fighter1: # Fallback for minions of P1?
                     # If summon, check master? For now, assume minion shares team logic via name or data
                     if "Wolf" in c.name or "Construct" in c.name:
                         # Assume minion matches summoner?
                         # Simplified: If not P1, assume Enemy for now unless stated
                         if c.name not in [self.fighter1.name]:
                             col = COLOR_P2
                
                pygame.draw.circle(self.screen, col, (cx + TILE_SIZE//2, cy + TILE_SIZE//2), TILE_SIZE//3)
                
                # HP Bar
                if c.max_hp > 0:
                    pct = max(0, min(1, c.hp / c.max_hp))
                    pygame.draw.rect(self.screen, (255,0,0), (cx+5, cy-8, 40, 5))
                    pygame.draw.rect(self.screen, (0,255,0), (cx+5, cy-8, 40*pct, 5))
                
                # Status Effect Icons (compact text)
                status_icons = []
                if c.is_stunned: status_icons.append("STN")
                if c.is_poisoned: status_icons.append("PSN")
                if c.is_frightened: status_icons.append("FRG")
                if c.is_charmed: status_icons.append("CHM")
                if c.is_paralyzed: status_icons.append("PRL")
                if c.is_prone: status_icons.append("PRN")
                if c.is_blinded: status_icons.append("BLD")
                if c.is_grappled: status_icons.append("GRP")
                if c.is_restrained: status_icons.append("RST")
                if c.is_sanctuary: status_icons.append("SNC")
                if c.is_confused: status_icons.append("CNF")
                if c.is_berserk: status_icons.append("BRK")
                
                if status_icons:
                    status_text = " ".join(status_icons[:3]) # Limit to 3 shown
                    status_surf = self.font.render(status_text, True, (255, 200, 50))
                    self.screen.blit(status_surf, (cx, cy + TILE_SIZE - 10))

            # 3. HUD
            pygame.draw.rect(self.screen, (10,10,20), (0, 600, SCREEN_W, 100))
            for i, line in enumerate(reversed(self.log_lines[-6:])):
                col = (255,255,255)
                if "HIT" in line: col = (255,100,100)
                if "CLASH" in line: col = (255,255,100)
                img = self.font.render(line, True, col)
                self.screen.blit(img, (20, 680 - i*15))

            if self.engine.clash_active:
                 s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                 s.fill((0,0,0,180))
                 self.screen.blit(s, (0,0))
                 self.screen.blit(self.header_font.render("CLASH TRIGGERED!", True, (255,50,50)), (400, 300))
            
            # Sidebar HUD Draw
            self.draw_sidebar_hud()

        if self.state == "SHEET":
            self.draw_character_sheet()

        # Buttons
        if self.state == "SELECT":
             self.screen.blit(self.header_font.render("Select Map Layout", True, (255,255,255)), (50, 20))
        
        elif self.state == "COMBAT":
             pass

        for b in self.buttons: b.draw(self.screen, self.font)
        
        # Draw Context Menu
        if self.context_menu:
            cx, cy = self.context_menu["pos"]
            opts = self.context_menu["options"]
            w, h = 150, len(opts) * 30
            
            # Shadow
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((0,0,0,100))
            self.screen.blit(s, (cx+5, cy+5))
            
            # Bg
            pygame.draw.rect(self.screen, (40, 40, 50), (cx, cy, w, h))
            pygame.draw.rect(self.screen, (200, 200, 200), (cx, cy, w, h), 1)
            
            mx, my = pygame.mouse.get_pos()
            
            for i, (label, _, _) in enumerate(opts):
                rect = pygame.Rect(cx, cy + i*30, w, 30)
                col = (60, 60, 70)
                if rect.collidepoint((mx, my)): col = (80, 80, 100)
                
                pygame.draw.rect(self.screen, col, rect)
                pygame.draw.line(self.screen, (100, 100, 100), (cx, rect.bottom-1), (cx+w, rect.bottom-1))
                
                txt = self.font.render(label, True, (255, 255, 255))
                self.screen.blit(txt, (cx + 10, cy + i*30 + 5))

        pygame.display.flip()

    def draw_sidebar_hud(self):
        # Background
        pygame.draw.rect(self.screen, (25, 25, 35), (700, 0, 300, 700))
        pygame.draw.line(self.screen, (100, 100, 100), (700, 0), (700, 700), 2)
        
        c = self.engine.get_active_char()
        if not c: return
        
        x = 710; y = 20
        # Name
        self.screen.blit(self.header_font.render(c.name, True, (255,255,255)), (x, y)); y+=30
        
        # Bars Helper
        def draw_bar(label, cur, max_val, color, by):
            # Label
            self.screen.blit(self.font.render(label, True, (200,200,200)), (x, by))
            # Bar Bg
            pygame.draw.rect(self.screen, (50,50,50), (x+40, by, 200, 15))
            # Bar Fill
            pct = 0
            if max_val > 0: pct = max(0, min(1, cur / max_val))
            pygame.draw.rect(self.screen, color, (x+40, by, 200*pct, 15))
            # Text
            self.screen.blit(self.font.render(f"{cur}/{max_val}", True, (255,255,255)), (x+100, by-1))
            return by + 25
            
        y = draw_bar("HP", c.hp, c.max_hp, (200,50,50), y)
        y = draw_bar("SP", c.sp, c.max_sp, (50,200,50), y)
        y = draw_bar("FP", c.fp, c.max_fp, (50,50,250), y)
        y = draw_bar("CMP", c.cmp, c.max_cmp, (200,50,200), y)

    def open_sheet(self):
        active = self.engine.get_active_char()
        if active:
            self.sheet_target = active
            self.state = "SHEET"
            self.buttons = [Button((SCREEN_W-150, 10, 100, 40), "BACK", self.close_sheet)]

    def close_sheet(self):
        self.state = "COMBAT"
        self.scan_saves() # Reload combat buttons

    def open_inventory(self):
        active = self.engine.get_active_char()
        if active:
            self.inv_target = active
            self.state = "INVENTORY"
            self.buttons = [Button((SCREEN_W-150, 10, 100, 40), "BACK", self.close_inventory)]

    def close_inventory(self):
        self.state = "COMBAT"
        self.scan_saves()

    def draw_inventory_screen(self):
        c = self.inv_target
        if not c: return
        
        self.screen.fill((30, 30, 40))
        self.screen.blit(self.header_font.render(f"{c.name}'s INVENTORY", True, (255, 255, 255)), (50, 20))
        
        y = 80
        # Equipped Items
        self.screen.blit(self.header_font.render("EQUIPPED:", True, (200, 200, 100)), (50, y)); y += 35
        if c.inventory:
            for slot, item in c.inventory.equipped.items():
                if item:
                    txt = f"  {slot}: {item.name}"
                    color = (100, 255, 100)
                else:
                    txt = f"  {slot}: (Empty)"
                    color = (100, 100, 100)
                self.screen.blit(self.font.render(txt, True, color), (50, y)); y += 25
        else:
            self.screen.blit(self.font.render("  No inventory system", True, (255, 100, 100)), (50, y)); y += 25
        
        y += 20
        # All Items in Bag
        self.screen.blit(self.header_font.render("BAG:", True, (200, 200, 100)), (50, y)); y += 35
        if c.inventory and c.inventory.items:
            for item_name in c.inventory.items:
                self.screen.blit(self.font.render(f"  - {item_name}", True, (200, 200, 200)), (50, y)); y += 22
        else:
            self.screen.blit(self.font.render("  (Empty)", True, (100, 100, 100)), (50, y)); y += 25
        
        # Instructions
        self.screen.blit(self.font.render("Weapons from Builder are auto-equipped to Main Hand.", True, (150, 150, 150)), (50, 550))

    def draw_character_sheet(self):
        c = self.sheet_target
        if not c: return
        
        # Background
        pygame.draw.rect(self.screen, (30,30,40), (50, 50, SCREEN_W-100, SCREEN_H-100))
        pygame.draw.rect(self.screen, (200,200,200), (50, 50, SCREEN_W-100, SCREEN_H-100), 2)
        
        # Header
        name_txt = self.header_font.render(f"{c.name} ({c.data.get('Species', 'Unknown')})", True, (255,255,255))
        self.screen.blit(name_txt, (80, 80))
        
        # Stats Column
        y = 130
        self.screen.blit(self.header_font.render("ATTRIBUTES", True, (200,200,100)), (80, y)); y+=30
        for stat in ["Might", "Reflexes", "Endurance", "Knowledge", "Willpower", "Intuition", "Logic", "Fortitude", "Charm", "Vitality"]:
            score = c.get_stat(stat)
            mod = c.get_stat_modifier(stat)
            txt = f"{stat}: {score} ({'+' if mod>=0 else ''}{mod})"
            self.screen.blit(self.font.render(txt, True, (220,220,220)), (80, y))
            y += 25
            
        # Derived Column
        y = 130; x = 350
        self.screen.blit(self.header_font.render("STATUS", True, (200,200,100)), (x, y)); y+=30
        self.screen.blit(self.font.render(f"HP: {c.hp}/{c.max_hp}", True, (255,100,100)), (x, y)); y+=25
        self.screen.blit(self.font.render(f"SP: {c.sp}/{c.max_sp}", True, (100,255,100)), (x, y)); y+=25
        self.screen.blit(self.font.render(f"FP: {c.fp}/{c.max_fp}", True, (100,100,255)), (x, y)); y+=25
        self.screen.blit(self.font.render(f"CMP: {c.cmp}/{c.max_cmp}", True, (200,100,200)), (x, y)); y+=25
        self.screen.blit(self.font.render(f"Move: {c.movement_remaining}/{c.movement}", True, (200,200,200)), (x, y)); y+=25
        
        # Status Effects
        y += 20
        self.screen.blit(self.header_font.render("ACTIVE EFFECTS", True, (200,200,100)), (x, y)); y+=30
        if not c.active_effects:
             self.screen.blit(self.font.render("None", True, (150,150,150)), (x, y))
        else:
             for eff in c.active_effects:
                 self.screen.blit(self.font.render(f"- {eff['name']} ({eff['duration']} rds)", True, (255,200,100)), (x, y)); y+=20

        # Gear Column
        y = 130; x = 600
        self.screen.blit(self.header_font.render("EQUIPMENT", True, (200,200,100)), (x, y)); y+=30
        if c.inventory:
            for slot, item in c.inventory.equipped.items():
                if item:
                    txt = f"{slot}: {item.name}"
                    # Stats?
                    stats = []
                    if slot == "Main Hand": stats.append(f"{c.inventory.get_weapon_stats()[0]}")
                    if slot == "Armor": stats.append(f"AC?")
                    
                    self.screen.blit(self.font.render(txt, True, (255,255,255)), (x, y)); y+=20
                    self.screen.blit(self.font.render(f"   {', '.join(stats)}", True, (150,150,150)), (x, y)); y+=25
                else:
                    self.screen.blit(self.font.render(f"{slot}: (Empty)", True, (100,100,100)), (x, y)); y+=25
                    
        # Skills
        y += 20
        self.screen.blit(self.header_font.render("SKILLS", True, (200,200,100)), (x, y)); y+=30
        skills = c.skills if isinstance(c.skills, dict) else {k: 0 for k in c.skills}
        for s, rank in skills.items():
             self.screen.blit(self.font.render(f"{s}: Rank {rank}", True, (200,220,255)), (x, y)); y+=20
             self.screen.blit(self.header_font.render("Select Map Layout", True, (255,255,255)), (50, 20))

        for b in self.buttons: b.draw(self.screen, self.font)
        
        pygame.display.flip()

    def cheat_give_xp(self):
        if self.fighter1:
            self.fighter1.xp += 100
            if hasattr(self.fighter1, 'save_state'):
                self.fighter1.save_state()
            self.log_lines.append(f"Granted 100 XP to {self.fighter1.name}. Total: {self.fighter1.xp}")
            self.scan_saves() # Refresh UI

    def train_fighter(self):
        if not self.fighter1: return
        
        # Initialize Progression
        if mechanics.ProgressionEngine:
             pe = mechanics.ProgressionEngine()
             # Example: Try to upgrade "The Great Weapons" (common check)
             # Heuristic: Find first skill in dictionary to upgrade
             if isinstance(self.fighter1.skills, dict) and self.fighter1.skills:
                 skill = list(self.fighter1.skills.keys())[0] # Just pick first one for test
             else:
                 skill = "The Great Weapons" 
                 
             self.log_lines.append(f"Attempting to train: {skill}...")
             success, msg = pe.buy_skill_rank(self.fighter1, skill)
             self.log_lines.append(msg)
             self.scan_saves()
        else:
             self.log_lines.append("Progression Engine not available.")

    def toggle_p2_ai(self):
        if not self.fighter2: return
        current = self.fighter2.data.get("AI")
        if current:
            # Switch to Manual
            del self.fighter2.data["AI"]
        else:
            # Switch to AI (Default Aggressive)
            self.fighter2.data["AI"] = self.selected_ai_template
        self.scan_saves()

    def toggle_p1_ai(self):
        if not self.fighter1: return
        current = self.fighter1.data.get("AI")
        if current:
            # Switch to Manual
            del self.fighter1.data["AI"]
        else:
            # Switch to AI
            self.fighter1.data["AI"] = "Aggressive" # Default for P1
        self.scan_saves()

if __name__ == "__main__":
    ArenaApp().run()
