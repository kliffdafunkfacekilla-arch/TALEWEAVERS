import { useEffect, useRef, useState } from 'react';
import { Application, Container, Graphics, Assets, Sprite, Texture, Rectangle } from 'pixi.js';
import { Entity, MapData } from '../types';

interface MapCanvasProps {
    mapData: any;
    entities: any[];
    onCellClick: (x: number, y: number) => void;
    onCellDrag?: (x: number, y: number) => void;
}

const SHEET_CONFIG = {
    url: '/spritesheet.png',
    spriteWidth: 32,
    spriteHeight: 32,
};

export function MapCanvas({ mapData, entities, onCellClick }: MapCanvasProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const [isReady, setIsReady] = useState(false);
    const texturesCache = useRef<Map<number, Texture>>(new Map());

    useEffect(() => {
        if (!containerRef.current) return;

        const app = new Application();
        let resizeObserver: ResizeObserver | null = null;
        let isDestroyed = false;

        const init = async () => {
            console.log("[TALEWEAVERS] MapCanvas V3 (Clean Lifecycle) Initializing...");
            try {
                // Initialize Pixi
                await app.init({
                    background: '#0f0f13',
                    antialias: true,
                    resolution: window.devicePixelRatio || 1,
                    resizeTo: containerRef.current || undefined, // Use built-in resize first
                });

                if (isDestroyed) {
                    app.destroy(true, { children: true, texture: true });
                    return;
                }

                if (containerRef.current) {
                    containerRef.current.appendChild(app.canvas);
                    appRef.current = app;
                }

                // Load Assets
                await Assets.load(SHEET_CONFIG.url);

                if (!isDestroyed) {
                    setIsReady(true);
                }
            } catch (e) {
                console.error("Pixi Init Error:", e);
                // Even on error, we might be able to render something if app.renderer exists
                if (!isDestroyed) setIsReady(true);
            }
        };

        init();

        return () => {
            isDestroyed = true;
            if (resizeObserver) resizeObserver.disconnect();

            // Critical: Pixi v8 destruction safety
            const cleanUp = async () => {
                if (appRef.current) {
                    const toDestroy = appRef.current;
                    appRef.current = null;
                    try {
                        toDestroy.destroy(true, { children: true, texture: true });
                    } catch (err) {
                        console.warn("Pixi Destroy Error:", err);
                    }
                } else {
                    try {
                        app.destroy(true, { children: true, texture: true });
                    } catch (err) {
                        // Ignore errors during early destruction
                    }
                }
            };
            cleanUp();
        };
    }, []);

    const getTexture = (index: number): Texture | null => {
        try {
            if (texturesCache.current.has(index)) return texturesCache.current.get(index)!;
            const base = Assets.get<Texture>(SHEET_CONFIG.url);
            if (!base || !base.source) return null;

            const cols = Math.floor(base.width / SHEET_CONFIG.spriteWidth);
            const col = index % cols;
            const row = Math.floor(index / cols);

            const tex = new Texture({
                source: base.source,
                frame: new Rectangle(col * 32, row * 32, 32, 32)
            });
            texturesCache.current.set(index, tex);
            return tex;
        } catch (e) {
            return null;
        }
    };

    // Render logic
    useEffect(() => {
        const app = appRef.current;
        if (!app || !app.stage || !isReady) return;

        app.stage.removeChildren();
        const world = new Container();
        app.stage.addChild(world);

        const TILE = 40;

        // 1. Static Background
        const bgLayer = new Container();
        world.addChild(bgLayer);

        mapData.grid.forEach((row, y) => {
            row.forEach((cell, x) => {
                const tex = getTexture(cell);
                let tile;
                if (tex) {
                    tile = new Sprite(tex);
                    tile.width = TILE;
                    tile.height = TILE;
                } else {
                    const g = new Graphics().rect(0, 0, TILE, TILE).fill(cell === 896 ? 0x222222 : 0x111111);
                    tile = g;
                }
                tile.x = x * TILE;
                tile.y = y * TILE;
                bgLayer.addChild(tile);
            });
        });

        bgLayer.interactive = true;
        let isDragging = false;

        bgLayer.on('pointerdown', (e) => {
            isDragging = true;
            const p = e.getLocalPosition(world);
            onCellClick(Math.floor(p.x / TILE), Math.floor(p.y / TILE));
        });

        bgLayer.on('pointermove', (e) => {
            if (isDragging && onCellDrag) {
                const p = e.getLocalPosition(world);
                onCellDrag(Math.floor(p.x / TILE), Math.floor(p.y / TILE));
            }
        });

        bgLayer.on('pointerup', () => isDragging = false);
        bgLayer.on('pointerupoutside', () => isDragging = false);

        // 2. Entities
        const entLayer = new Container();
        world.addChild(entLayer);

        entities.forEach(ent => {
            const eGroup = new Container();
            const sheetMatch = ent.icon?.match(/sheet:(\d+)/);
            const index = sheetMatch ? parseInt(sheetMatch[1]) : 5074;
            const tex = getTexture(index);

            if (tex) {
                const s = new Sprite(tex);
                s.anchor.set(0.5);
                s.width = TILE * 0.8;
                s.height = TILE * 0.8;
                eGroup.addChild(s);
            }

            eGroup.x = ent.pos[0] * TILE + TILE / 2;
            eGroup.y = ent.pos[1] * TILE + TILE / 2;

            if (ent.hp !== undefined) {
                const hpBar = new Graphics().rect(-15, 18, 30, 4).fill(0x333333).rect(-15, 18, 30 * (ent.hp / (ent.maxHp || 100)), 4).fill(0x22c55e);
                eGroup.addChild(hpBar);
            }
            entLayer.addChild(eGroup);
        });

        // Initial Centering
        world.x = (app.renderer.width - mapData.width * TILE) / 2;
        world.y = (app.renderer.height - mapData.height * TILE) / 2;

    }, [mapData, entities, isReady]);

    return <div ref={containerRef} className="w-full h-full bg-[#0f0f13] overflow-hidden" />;
}
