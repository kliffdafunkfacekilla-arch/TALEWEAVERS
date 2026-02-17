import math

class WorldCoords:
    """
    Handles 4-Tier Hierarchical Coordinates for T.A.L.E.W.E.A.V.E.R.S.
    Hierachy: Global (126) -> Regional (1:1) -> Local (100x100) -> Player (100x100)
    """
    
    def __init__(self, g_idx=0, l_x=50, l_y=50, p_x=50, p_y=50):
        self.g_idx = g_idx  # 0-125
        self.l_x = l_x      # 0-99
        self.l_y = l_y      # 0-99
        self.p_x = p_x      # 0-99
        self.p_y = p_y      # 0-99

    def to_dict(self):
        return {
            "g": self.g_idx,
            "l": [self.l_x, self.l_y],
            "p": [self.p_x, self.p_y]
        }

    def move_player(self, dx, dy):
        """Relative movement at the Player level with Local-level overflow."""
        self.p_x += dx
        self.p_y += dy
        
        # Handle Player X Overflow -> Local X
        while self.p_x >= 100:
            self.p_x -= 100
            self.l_x += 1
        while self.p_x < 0:
            self.p_x += 100
            self.l_x -= 1
            
        # Handle Player Y Overflow -> Local Y
        while self.p_y >= 100:
            self.p_y -= 100
            self.l_y += 1
        while self.p_y < 0:
            self.p_y += 100
            self.l_y -= 1
            
        # Clamp Local Coords (Global transitions happen at Regional borders)
        self.l_x = max(0, min(99, self.l_x))
        self.l_y = max(0, min(99, self.l_y))

    def move_local(self, dx, dy):
        """Movement at the Local level."""
        self.l_x = max(0, min(99, self.l_x + dx))
        self.l_y = max(0, min(99, self.l_y + dy))

def get_time_step(level):
    """Returns the time step description for each level."""
    steps = {
        "global": "Monthly",
        "regional": "Weekly",
        "local": "Daily",
        "player": "Hourly/Frozen"
    }
    return steps.get(level.lower(), "Unknown")
