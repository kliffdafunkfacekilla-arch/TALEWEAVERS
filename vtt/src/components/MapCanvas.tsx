import { useEffect, useRef, useState } from 'react';
import { Application, Container, Graphics, Text, Assets, Sprite, Texture, Rectangle, SCALE_MODES } from 'pixi.js';
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
                background: '#09090b', // Deep Onyx
                resizeTo: containerRef.current!,
                antialias: false, // Better for pixel art
                resolution: window.devicePixelRatio || 1,
            });

            if (containerRef.current) {
                containerRef.current.appendChild(app.canvas);
                appRef.current = app;
            }

            // Load Sprite Sheet with Pixel Filtering
            try {
                const sheet = await Assets.load(SHEET_CONFIG.url);
                if (sheet.source) {
                    sheet.source.scaleMode = 'nearest'; // ENSURE PIXEL ART CRISPNESS
                }
                setIsLoaded(true);
            } catch (e) {
                console.error("Failed to load spritesheet:", e);
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

        // Clear stage for fresh redraw
        app.stage.removeChildren();

        const TILE_SIZE = 48; // Scaled up for better visibility
        const worldContainer = new Container();
        app.stage.addChild(worldContainer);

        // 1. Draw Map Layer
        const floorContainer = new Container();
        mapData.grid.forEach((row, y) => {
            row.forEach((cell, x) => {
                const tex = getTexture(cell);
                let tile;

                if (tex) {
                    tile = new Sprite(tex);
                    tile.width = TILE_SIZE;
                    tile.height = TILE_SIZE;
                    tile.x = x * TILE_SIZE;
                    tile.y = y * TILE_SIZE;
                } else {
                    const graphics = new Graphics();
                    const color = cell === 896 ? 0x18181b : 0x09090b;
                    graphics.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                    graphics.fill(color);
                    graphics.stroke({ width: 0.5, color: 0x27272a });
                    tile = graphics;
                }
                floorContainer.addChild(tile);
            });
        });

        floorContainer.interactive = true;
        floorContainer.on('pointerdown', (e) => {
            const localPos = e.getLocalPosition(worldContainer);
            const gx = Math.floor(localPos.x / TILE_SIZE);
            const gy = Math.floor(localPos.y / TILE_SIZE);
            if (gx >= 0 && gy >= 0) onCellClick(gx, gy);
        });

        worldContainer.addChild(floorContainer);

        // 2. Draw Entities Layer
        entities.forEach(ent => {
            const entGroup = new Container();
            const [ex, ey] = ent.pos;

            // UV Sprite Selection
            let visual;
            const sheetMatch = ent.icon?.match(/sheet:(\d+)/);

            if (sheetMatch) {
                const index = parseInt(sheetMatch[1]);
                const tex = getTexture(index);
                if (tex) {
                    visual = new Sprite(tex);
                    visual.anchor.set(0.5);
                    visual.width = TILE_SIZE * 0.9;
                    visual.height = TILE_SIZE * 0.9;
                }
            }

            // Fallback High-Quality Placeholder
            if (!visual) {
                const fallback = new Graphics();
                const color = ent.type === 'player' ? 0x22d3ee : (ent.type === 'enemy' ? 0xf43f5e : 0x10b981);
                fallback.circle(0, 0, TILE_SIZE * 0.4);
                fallback.fill({ color, alpha: 0.8 });
                fallback.stroke({ width: 2, color: 0xffffff });
                visual = fallback;
            }

            // Micro-animation: Hover "Breathing"
            let tick = Math.random() * 100;
            app.ticker.add((delta) => {
                tick += 0.05 * delta.deltaTime;
                entGroup.scale.set(1 + Math.sin(tick) * 0.02);
            });

            entGroup.addChild(visual);
            entGroup.x = ex * TILE_SIZE + TILE_SIZE / 2;
            entGroup.y = ey * TILE_SIZE + TILE_SIZE / 2;

            // Premium Vital Bars
            if (ent.hp !== undefined && ent.maxHp) {
                const hpPct = Math.max(0, Math.min(1, ent.hp / ent.maxHp));
                const bar = new Graphics();

                // Background
                bar.rect(-18, 20, 36, 6);
                bar.fill(0x18181b);

                // Progress
                bar.rect(-18, 20, 36 * hpPct, 6);
                const barColor = hpPct > 0.6 ? 0x22c55e : (hpPct > 0.3 ? 0xeab308 : 0xef4444);
                bar.fill(barColor);

                // Border
                bar.stroke({ width: 1, color: 0x3f3f46 });
                entGroup.addChild(bar);
            }

            // Glowing Tint for Active/Selected?
            if (ent.type === 'player') {
                const glow = new Graphics();
                glow.circle(0, 0, TILE_SIZE * 0.45);
                glow.stroke({ width: 4, color: 0x22d3ee, alpha: 0.3 });
                entGroup.addChildAt(glow, 0);
            }

            // Stylized Name Tag
            if (ent.name) {
                const label = new Text({
                    text: ent.name.split(' ')[0], // First name only for brevity
                    style: {
                        fontFamily: 'Inter, system-ui, sans-serif',
                        fontSize: 11,
                        fontWeight: 'bold',
                        fill: 0xffffff,
                        stroke: { color: 0x000000, width: 3 },
                        dropShadow: { color: 0x000000, alpha: 0.5, blur: 2, distance: 1 }
                    }
                });
                label.anchor.set(0.5, 1);
                label.y = -20;
                entGroup.addChild(label);
            }

            worldContainer.addChild(entGroup);
        });

        // 3. Dynamic Camera Management
        const padding = 100;
        const availableWidth = app.screen.width - padding;
        const availableHeight = app.screen.height - padding;
        const worldWidth = (mapData.width || 12) * TILE_SIZE;
        const worldHeight = (mapData.height || 12) * TILE_SIZE;

        const scaleX = availableWidth / worldWidth;
        const scaleY = availableHeight / worldHeight;
        const finalScale = Math.min(1, scaleX, scaleY); // Don't zoom in past 1:1

        worldContainer.scale.set(finalScale);
        worldContainer.x = (app.screen.width - worldWidth * finalScale) / 2;
        worldContainer.y = (app.screen.height - worldHeight * finalScale) / 2;

    }, [mapData, entities, isLoaded, appRef.current]);

    return (
        <div
            ref={containerRef}
            className="w-full h-full bg-[#09090b] rounded-xl border border-zinc-800 shadow-2xl overflow-hidden relative"
        >
            {/* Ambient UI Overlay */}
            <div className="absolute top-4 left-4 pointer-events-none">
                <div className="bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-zinc-700 text-xs text-zinc-400 font-mono">
                    TACTICAL GRID: {mapData.width}x{mapData.height}
                </div>
            </div>
        </div>
    );
}
