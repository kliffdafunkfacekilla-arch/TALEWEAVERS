import { useEffect, useRef, useState } from 'react';
import { Application, Container, Graphics, Text, Assets, Sprite, Texture, Rectangle } from 'pixi.js';
import { Entity, MapData } from '../types';

interface MapCanvasProps {
    mapData: MapData;
    entities: Entity[];
    onCellClick: (x: number, y: number) => void;
}

// Configuration for the Sprite Sheet
const SHEET_CONFIG = {
    url: '/spritesheet.png',
    spriteWidth: 32,
    spriteHeight: 32,
    padding: 0
};

export function MapCanvas({ mapData, entities, onCellClick }: MapCanvasProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const texturesCache = useRef<Map<number, Texture>>(new Map());

    // Initialize Pixi App and Load Assets
    useEffect(() => {
        if (!containerRef.current) return;

        const app = new Application();

        const initApp = async () => {
            await app.init({
                background: '#0f0f13',
                resizeTo: containerRef.current!,
                antialias: true,
                resolution: window.devicePixelRatio || 1,
            });

            if (containerRef.current) {
                containerRef.current.appendChild(app.canvas);
                appRef.current = app;
            }

            // Load Sprite Sheet
            try {
                await Assets.load(SHEET_CONFIG.url);
                setIsLoaded(true);
            } catch (e) {
                console.error("Failed to load spritesheet:", e);
                // Fallback to graphics if sheet is missing
                setIsLoaded(true);
            }
        };

        initApp();

        return () => {
            app.destroy(true, { children: true, texture: true });
        };
    }, []);

    // Helper to get a texture from the sheet by index
    const getTexture = (index: number): Texture | null => {
        if (texturesCache.current.has(index)) return texturesCache.current.get(index)!;

        const baseTexture = Assets.get(SHEET_CONFIG.url);
        if (!baseTexture) return null;

        const cols = Math.floor(baseTexture.width / SHEET_CONFIG.spriteWidth);
        const col = index % cols;
        const row = Math.floor(index / cols);

        const rect = new Rectangle(
            col * SHEET_CONFIG.spriteWidth,
            row * SHEET_CONFIG.spriteHeight,
            SHEET_CONFIG.spriteWidth,
            SHEET_CONFIG.spriteHeight
        );

        const tex = new Texture({
            source: baseTexture,
            frame: rect
        });

        texturesCache.current.set(index, tex);
        return tex;
    };

    // Render Loop (Reactive)
    useEffect(() => {
        const app = appRef.current;
        if (!app || !app.stage || !isLoaded) return;

        app.stage.removeChildren();

        const TILE_SIZE = 40;
        const gridContainer = new Container();
        app.stage.addChild(gridContainer);

        // 1. Draw Grid
        const gridGraphics = new Graphics();

        mapData.grid.forEach((row, y) => {
            row.forEach((cell, x) => {
                const isWall = cell === 1;

                // If we have a spritesheet, we could use indices for walls (e.g., index 1) and floors (index 0)
                // For now, let's stick to colored rectangles but enable sprite support easily
                const color = isWall ? 0x2a2b36 : 0x1a1b26;
                gridGraphics.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.fill(color);
                gridGraphics.stroke({ width: 0.5, color: 0x333344 });
            });
        });

        gridGraphics.interactive = true;
        gridGraphics.on('pointerdown', (e) => {
            const localPos = e.getLocalPosition(gridContainer);
            const gx = Math.floor(localPos.x / TILE_SIZE);
            const gy = Math.floor(localPos.y / TILE_SIZE);
            if (gx >= 0 && gy >= 0) onCellClick(gx, gy);
        });

        gridContainer.addChild(gridGraphics);

        // 2. Draw Entities
        entities.forEach(ent => {
            const entityContainer = new Container();
            const [ex, ey] = ent.pos;

            // TRY LOAD FROM SHEET
            let visual;
            const sheetMatch = ent.icon?.match(/sheet:(\d+)/);

            if (sheetMatch && isLoaded) {
                const index = parseInt(sheetMatch[1]);
                const tex = getTexture(index);
                if (tex) {
                    visual = new Sprite(tex);
                    visual.anchor.set(0.5);
                    visual.width = TILE_SIZE * 0.9;
                    visual.height = TILE_SIZE * 0.9;
                }
            }

            // FALLBACK TO CIRCLE
            if (!visual) {
                const circle = new Graphics();
                const color = ent.type === 'player' ? 0x60a5fa : (ent.type === 'enemy' ? 0xef4444 : 0x10b981);
                circle.circle(0, 0, TILE_SIZE * 0.4);
                circle.fill(color);
                circle.stroke({ width: 2, color: 0xffffff });
                visual = circle;
            }

            entityContainer.addChild(visual);
            entityContainer.x = ex * TILE_SIZE + TILE_SIZE / 2;
            entityContainer.y = ey * TILE_SIZE + TILE_SIZE / 2;

            // HP Bar
            if (ent.hp !== undefined && ent.maxHp) {
                const hpPercent = ent.hp / ent.maxHp;
                const bar = new Graphics();
                const pct = Math.max(0, Math.min(1, hpPercent));

                bar.rect(-15, 18, 30, 4);
                bar.fill(0x333333);
                bar.rect(-15, 18, 30 * pct, 4);
                bar.fill(evtColorResponse(pct));
                entityContainer.addChild(bar);
            }

            // Name Tag
            if (ent.name) {
                const text = new Text({
                    text: ent.name,
                    style: {
                        fontFamily: 'Arial',
                        fontSize: 10,
                        fill: 0xffffff,
                        stroke: { color: 0x000000, width: 2 },
                        align: 'center'
                    }
                });
                text.anchor.set(0.5, 1);
                text.y = -18;
                entityContainer.addChild(text);
            }

            gridContainer.addChild(entityContainer);
        });

        // Center View
        const gridSizeX = (mapData.width || 20) * TILE_SIZE;
        const gridSizeY = (mapData.height || 20) * TILE_SIZE;
        gridContainer.x = (app.screen.width - gridSizeX) / 2;
        gridContainer.y = (app.screen.height - gridSizeY) / 2;

    }, [mapData, entities, isLoaded, appRef.current]);

    return <div ref={containerRef} className="w-full h-full bg-[#0f0f13] overflow-hidden" />;
}

function evtColorResponse(pct: number) {
    if (pct > 0.6) return 0x22c55e;
    if (pct > 0.3) return 0xeab308;
    return 0xef4444;
}
