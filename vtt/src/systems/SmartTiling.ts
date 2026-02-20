/**
 * SmartTiling System
 * Uses 4-bit bitmasking (16 tiles) to determine the correct joined texture
 * for connected terrain like walls, roads, mountains, or water.
 * 
 * Bit configuration:
 * 1 (North)
 * 2 (West)
 * 4 (East)
 * 8 (South)
 */

export function calculateBitmask(
    grid: number[][],
    x: number,
    y: number,
    targetTileIndex: number
): number {
    let mask = 0;
    const height = grid.length;
    const width = height > 0 ? grid[0].length : 0;

    // Check North
    if (y > 0 && grid[y - 1][x] === targetTileIndex) {
        mask += 1;
    }
    // Check West
    if (x > 0 && grid[y][x - 1] === targetTileIndex) {
        mask += 2;
    }
    // Check East
    if (x < width - 1 && grid[y][x + 1] === targetTileIndex) {
        mask += 4;
    }
    // Check South
    if (y < height - 1 && grid[y + 1][x] === targetTileIndex) {
        mask += 8;
    }

    return mask;
}

/**
 * Returns the adjusted tile index based on the calculated bitmask.
 * Assuming a local spritesheet layout where the 16 variations 
 * of a connected tile are arranged consecutively starting from the base index.
 */
export function getSmartTileIndex(
    grid: number[][],
    x: number,
    y: number,
    baseIndex: number
): number {
    const mask = calculateBitmask(grid, x, y, baseIndex);
    
    // For this implementation, we assume that the 16 tile variations 
    // for a specific terrain type (like wall/water) are laid out 
    // sequentially in the sprite sheet, starting exactly at `baseIndex`.
    // Example: if water is 194, variations are 194 to 209 depending on connections.
    // By default, just return baseIndex + mask.
    return baseIndex + mask;
}
