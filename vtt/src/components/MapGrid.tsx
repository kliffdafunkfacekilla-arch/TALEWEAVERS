import React from 'react';
import { useGameStore } from '../store';
import clsx from 'clsx';

const TILE_SIZE = 48; // Pixels

export const MapGrid: React.FC = () => {
    const { map, entities, selectedEntityId, moveEntity, selectEntity, addLog } = useGameStore();

    const handleTileClick = (x: number, y: number) => {
        // Logic: If we have an entity selected, try to move it
        if (selectedEntityId) {
            const entity = entities.find(e => e.id === selectedEntityId);

            // Collision Check (Wall)
            if (map.grid[y] && map.grid[y][x] === 1) {
                addLog("Blocked! You cannot move into a wall.");
                return;
            }

            // Move
            if (entity) {
                moveEntity(selectedEntityId, [x, y]);
                selectEntity(null); // Deselect after move
            }
        }
    };

    const handleEntityClick = (e: React.MouseEvent, id: string) => {
        e.stopPropagation(); // Don't trigger tile click
        selectEntity(id);
        addLog(`Selected entity ${id}`);
    };

    return (
        <div
            className="relative bg-black border-4 border-gray-800 shadow-2xl"
            style={{
                width: map.width * TILE_SIZE,
                height: map.height * TILE_SIZE
            }}
        >
            {/* 1. RENDER TILES */}
            {map.grid.map((row, y) => (
                row.map((cellType, x) => {
                    // Determine Texture based on biome and cell type
                    let bgImage = '/floor/dirt_0_new.png';

                    if (cellType === 1) {
                        // Wall/Obstacle Logic
                        if (map.biome === 'forest') bgImage = '/trees/tree_1_red.png';
                        else if (map.biome === 'dungeon') bgImage = '/wall/brick_dark_0.png';
                        else bgImage = '/wall/cobalt_stone_1.png';
                    } else {
                        // Floor Logic
                        if (map.biome === 'forest') bgImage = '/floor/grass_0_new.png';
                        else if (map.biome === 'dungeon') bgImage = '/floor/black_cobalt_1.png';
                        else bgImage = '/floor/dirt_0_new.png';
                    }

                    return (
                        <div
                            key={`${x}-${y}`}
                            onClick={() => handleTileClick(x, y)}
                            className={clsx(
                                "absolute cursor-pointer hover:brightness-110",
                                cellType === 1 && "z-10" // Walls slightly higher visually if needed
                            )}
                            style={{
                                left: x * TILE_SIZE,
                                top: y * TILE_SIZE,
                                width: TILE_SIZE,
                                height: TILE_SIZE,
                                backgroundImage: `url(${bgImage})`,
                                backgroundSize: 'cover'
                            }}
                        />
                    );
                })
            ))}

            {/* 2. RENDER ENTITIES */}
            {entities.map((entity) => {
                const isObject = entity.type === 'object';
                const isEnemy = entity.type === 'enemy';

                return (
                    <div
                        key={entity.id}
                        onClick={(e) => {
                            e.stopPropagation();
                            selectEntity(entity.id);
                            if (isObject) {
                                useGameStore.getState().dmChat(`I interact with the ${entity.name}`);
                            } else {
                                addLog(`Selected ${entity.name}`);
                            }
                        }}
                        className={clsx(
                            "absolute z-20 transition-all duration-300 ease-in-out cursor-pointer",
                            selectedEntityId === entity.id && "scale-110",
                            selectedEntityId === entity.id && !isObject && "ring-2 ring-yellow-400",
                            selectedEntityId === entity.id && isObject && "ring-2 ring-blue-400"
                        )}
                        style={{
                            left: entity.pos[0] * TILE_SIZE,
                            top: entity.pos[1] * TILE_SIZE,
                            width: TILE_SIZE,
                            height: TILE_SIZE,
                        }}
                    >
                        {/* Entity Icon / Token */}
                        <img
                            src={`/${entity.icon}`}
                            alt={entity.name}
                            className={clsx(
                                "w-full h-full object-contain drop-shadow-md",
                                isObject && "scale-90" // Objects slightly smaller to fit grid nicely
                            )}
                            onError={(e) => {
                                e.currentTarget.src = isObject ? "/objects/chest_closed.png" : "/objects/npc.png";
                            }}
                        />

                        {/* Health Bar Mini (Only for living entities) */}
                        {!isObject && (
                            <div className="absolute -top-2 left-0 w-full h-1 bg-gray-700">
                                <div
                                    className={clsx(
                                        "h-full transition-all duration-500",
                                        isEnemy ? "bg-red-500" : "bg-green-500"
                                    )}
                                    style={{ width: `${(entity.hp / entity.maxHp) * 100}%` }}
                                />
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
};
