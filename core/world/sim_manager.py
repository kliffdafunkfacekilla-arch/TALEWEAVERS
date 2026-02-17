class SimulationManager:
    """
    Manages the 4-Tier Simulation Ticking Logic.
    Time Scales: Player (Hourly) -> Local (Daily) -> Regional (Weekly) -> Global (Monthly)
    """
    
    def __init__(self, state):
        self.state = state
        self.narrative_hours = 0
        
    def advance_time(self, hours):
        """Passes narrative time and triggers appropriate level simulation ticks."""
        self.narrative_hours += hours
        
        # Player Level: Every hour (Hourly)
        self.tick_player_sim(hours)
        
        # Local Level: Every 24 hours (Daily)
        if self.narrative_hours % 24 == 0:
            self.tick_local_sim()
            
        # Regional Level: Every 168 hours (7 days / Weekly)
        if self.narrative_hours % 168 == 0:
            self.tick_regional_sim()
            
        # Global Level: Every 672 hours (28 days / Monthly)
        if self.narrative_hours % 672 == 0:
            self.tick_global_sim()
            
    def tick_player_sim(self, hours):
        """High-detail tactical updates (Restoration, localized effects)."""
        print(f"[SIM] Player Level Tick: +{hours} hours")
        # Logic for healing, localized NPC movement, etc.

    def tick_local_sim(self):
        """Mid-detail updates (Caravans, mines, resources)."""
        print("[SIM] Local Level Tick: 1 Day Elapsed")
        # Logic for resource extraction, caravan movement.

    def tick_regional_sim(self):
        """Strategic updates (Borders, city growth, trade)."""
        print("[SIM] Regional Level Tick: 1 Week Elapsed")
        # Logic for faction influence shifts, infrastructure expansion.

    def tick_global_sim(self):
        """Macro-level updates (World trends, large-scale events)."""
        print("[SIM] Global Level Tick: 1 Month Elapsed")
        # Logic for massive disasters, technological shifts, global lore updates.

    def get_time_string(self):
        days = self.narrative_hours // 24
        remaining_hours = self.narrative_hours % 24
        return f"Day {days}, Hour {remaining_hours}"
