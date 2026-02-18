import { useEffect, useRef } from 'react';
import { Application, Container, Graphics, Text } from 'pixi.js';
import { Entity, MapData } from '../types';

interface MapCanvasProps {
    mapData: MapData;
    entities: Entity[];
    onCellClick: (x: number, y: number) => void;
}

export function MapCanvas({ mapData, entities, onCellClick }: MapCanvasProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);

    // Initialize Pixi App
    useEffect(() => {
        if (!containerRef.current) return;

        // Setup Application
        const app = new Application();

        // Async init for Pixi v8+
        const initApp = async () => {
            await app.init({
                background: '#1a1b26',
                resizeTo: containerRef.current!,
                antialias: true,
                resolution: window.devicePixelRatio || 1,
            });

            if (containerRef.current) {
                containerRef.current.appendChild(app.canvas);
                appRef.current = app;
            }
        };

        initApp();

        return () => {
            app.destroy(true, { children: true, texture: true, baseTexture: true });
        };
    }, []);

    // Render Loop (Reactive)
    useEffect(() => {
        const app = appRef.current;
        if (!app || !app.stage) return; // Wait for init

        // Clear Stage
        app.stage.removeChildren();

        const TILE_SIZE = 40;
        const gridContainer = new Container();
        app.stage.addChild(gridContainer);

        // 1. Draw Grid
        const graphics = new Graphics();

        mapData.grid.forEach((row, y) => {
            row.forEach((cell, x) => {
                const color = cell === 1 ? 0x2a2b36 : 0x1a1b26; // Wall vs Floor
                graphics.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                graphics.fill(color);
                graphics.stroke({ width: 1, color: 0x333344 });
            });
        });

        // Interactive - Click Handling
        gridContainer.interactive = true;

        // Note: Pixi v8 handles events differently, but for raw graphics we can attach to stage or container
        // if we make the graphics interactive.
        graphics.interactive = true;
        graphics.on('pointerdown', (e) => {
            const localPos = e.data.getLocalPosition(graphics);
            const gx = Math.floor(localPos.x / TILE_SIZE);
            const gy = Math.floor(localPos.y / TILE_SIZE);
            if (gx >= 0 && gy >= 0) onCellClick(gx, gy);
        });

        gridContainer.addChild(graphics);

        // 2. Draw Entities
        entities.forEach(ent => {
            const token = new Graphics();
            const [ex, ey] = ent.pos;

            const color = ent.type === 'player' ? 0x60a5fa : (ent.type === 'enemy' ? 0xef4444 : 0x10b981);

            token.circle(0, 0, TILE_SIZE * 0.4);
            token.fill(color);
            token.stroke({ width: 2, color: 0xffffff });

            token.x = ex * TILE_SIZE + TILE_SIZE / 2;
            token.y = ey * TILE_SIZE + TILE_SIZE / 2;

            // HP Bar
            if (ent.hp !== undefined && ent.maxHp) {
                const hpPercent = ent.hp / ent.maxHp;
                const bar = new Graphics();
                // Check valid percent
                const pct = Math.max(0, Math.min(1, hpPercent));

                bar.rect(-15, 18, 30, 4);
                bar.fill(0x333333); // bg
                bar.rect(-15, 18, 30 * pct, 4);
                bar.fill(evtColorResponse(pct)); // green to red

                token.addChild(bar);
            }

            // Name Tag
            if (ent.name) {
                const text = new Text({
                    text: ent.name, style: {
                        fontFamily: 'Arial',
                        fontSize: 10,
                        fill: 0xffffff,
                        align: 'center'
                    }
                });
                text.anchor.set(0.5, 1);
                text.y = -15;
                token.addChild(text);
            }

            gridContainer.addChild(token);
        });

        // Center View Logic (simplistic)
        const gridSizeX = (mapData.width || 20) * TILE_SIZE;
        const gridSizeY = (mapData.height || 20) * TILE_SIZE;

        gridContainer.x = (app.screen.width - gridSizeX) / 2;
        gridContainer.y = (app.screen.height - gridSizeY) / 2;

    }, [mapData, entities, appRef.current]); // Re-render when data changes

    return <div ref={containerRef} className="w-full h-full bg-[#0f0f13] overflow-hidden" />;
}

function evtColorResponse(pct: number) {
    if (pct > 0.6) return 0x22c55e;
    if (pct > 0.3) return 0xeab308;
    return 0xef4444;
}
