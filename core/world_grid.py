import os
import json

class WorldGrid:
    def __init__(self, width=100, height=100, save_path=None):
        self.width = width
        self.height = height
        self.save_path = save_path
        # Default Grass (128)
        self.grid = [[128 for _ in range(width)] for _ in range(height)]
        
        if save_path and os.path.exists(save_path):
            self.load()

    def load(self):
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                self.grid = data['grid']
                self.width = data['width']
                self.height = data['height']
        except Exception as e:
            print(f"[GRID] Load error: {e}")

    def save(self):
        if not self.save_path: return
        try:
            with open(self.save_path, 'w') as f:
                json.dump({
                    "width": self.width,
                    "height": self.height,
                    "grid": self.grid
                }, f)
        except Exception as e:
            print(f"[GRID] Save error: {e}")

    def paint(self, x, y, tile_index, radius=1):
        """Applies a circular brush of tile_index at (x, y)."""
        radius_sq = radius * radius
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius_sq:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self.grid[ny][nx] = tile_index
        return True
