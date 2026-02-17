import random

def generate_cellular_automata_map(width=40, height=40, wall_prob=0.4, iterations=4):
    """
    Generates a 2D grid map using Cellular Automata.
    0 = Floor, 1 = Wall
    """
    # 1. Random Noise
    grid = [[1 if random.random() < wall_prob else 0 for _ in range(width)] for _ in range(height)]
    
    # 2. Smooth iterations (4-5 rule)
    for _ in range(iterations):
        new_grid = [row[:] for row in grid]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Count neighbors
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0: continue
                        if grid[y+dy][x+dx] == 1:
                            neighbors += 1
                
                if neighbors > 4:
                    new_grid[y][x] = 1
                elif neighbors < 4:
                    new_grid[y][x] = 0
        grid = new_grid
    
    # 3. Ensure border walls
    for y in range(height):
        grid[y][0] = grid[y][width-1] = 1
    for x in range(width):
        grid[0][x] = grid[height-1][x] = 1
        
    return grid

if __name__ == "__main__":
    # Test print
    m = generate_cellular_automata_map()
    for row in m:
        print("".join(["#" if c == 1 else " " for c in row]))
