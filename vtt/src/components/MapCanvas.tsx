import { useEffect, useRef, useState, useMemo } from 'react';
import { Application, Container, Graphics, Assets, Sprite, Texture, Rectangle, Point, Text, TextStyle } from 'pixi.js';
import { clsx } from 'clsx';

interface MapCanvasProps {
    mapData: any;
    entities: any[];
    onCellClick: (x: number, y: number) => void;
    onCellHover?: (x: number, y: number | null) => void;
    range?: number;
    origin?: [number, number];
    visualEvents?: any[]; // Transient events like [{type: 'FCT', ...}]
}

const SHEET_CONFIG = {
    url: '/spritesheet.png',
    spriteWidth: 32,
    spriteHeight: 32,
};

export function MapCanvas({ mapData, entities, onCellClick, onCellHover, range, origin, visualEvents }: MapCanvasProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const worldRef = useRef<Container | null>(null);
    const entGroupRef = useRef<Map<string, Container>>(new Map());
    const [isReady, setIsReady] = useState(false);
    const texturesCache = useRef<Map<number, Texture>>(new Map());
    const TILE = 40;

    // 1. App Initialization
    useEffect(() => {
        if (!containerRef.current) return;
        const app = new Application();
        let isDestroyed = false;

        const init = async () => {
            try {
                await app.init({
                    background: '#0f0f13',
                    antialias: true,
                    resolution: window.devicePixelRatio || 1,
                    resizeTo: containerRef.current || undefined,
                });
                if (isDestroyed) { app.destroy(true); return; }
                if (containerRef.current) {
                    containerRef.current.appendChild(app.canvas);
                    appRef.current = app;
                }
                await Assets.load(SHEET_CONFIG.url);
                if (!isDestroyed) setIsReady(true);
            } catch (e) {
                console.error("Pixi Init Error:", e);
                if (!isDestroyed) setIsReady(true);
            }
        };
        init();

        return () => {
            isDestroyed = true;
            if (appRef.current) {
                appRef.current.destroy(true, { children: true, texture: true });
                appRef.current = null;
            }
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
        } catch (e) { return null; }
    };

    // 2. Main Render Loop
    useEffect(() => {
        const app = appRef.current;
        if (!app || !app.stage || !isReady) return;

        app.stage.removeChildren();
        const world = new Container();
        worldRef.current = world;
        app.stage.addChild(world);

        // Layers
        const bgLayer = new Container();
        const entLayer = new Container();
        const uiLayer = new Container();
        world.addChild(bgLayer, entLayer, uiLayer);

        // Centering
        world.x = (app.renderer.width - mapData.width * TILE) / 2;
        world.y = (app.renderer.height - mapData.height * TILE) / 2;

        // Static Grid
        mapData.grid.forEach((row: number[], y: number) => {
            row.forEach((cell: number, x: number) => {
                const tex = getTexture(cell);
                let tile;
                if (tex) {
                    tile = new Sprite(tex);
                    tile.width = TILE; tile.height = TILE;
                } else {
                    tile = new Graphics().rect(0, 0, TILE, TILE).fill(0x111111);
                }
                tile.x = x * TILE; tile.y = y * TILE;
                bgLayer.addChild(tile);
            });
        });

        // Entities
        entGroupRef.current.clear();
        entities.forEach(ent => {
            const eGroup = new Container();
            const sheetMatch = ent.icon?.match(/sheet:(\d+)/);
            const tex = getTexture(sheetMatch ? parseInt(sheetMatch[1]) : 5074);
            if (tex) {
                const s = new Sprite(tex);
                s.anchor.set(0.5);
                s.width = TILE * 0.8; s.height = TILE * 0.8;
                eGroup.addChild(s);
            }
            eGroup.x = ent.pos[0] * TILE + TILE / 2;
            eGroup.y = ent.pos[1] * TILE + TILE / 2;

            if (ent.hp !== undefined) {
                const hpBar = new Graphics().rect(-15, 18, 30, 4).fill(0x333333).rect(-15, 18, 30 * (ent.hp / (ent.maxHp || 100)), 4).fill(0x22c55e);
                eGroup.addChild(hpBar);
            }
            entLayer.addChild(eGroup);
            entGroupRef.current.set(ent.id, eGroup);
        });

        // Overlay & Interaction
        bgLayer.interactive = true;
        bgLayer.on('pointerdown', (e) => {
            const p = e.getLocalPosition(world);
            onCellClick(Math.floor(p.x / TILE), Math.floor(p.y / TILE));
        });

        bgLayer.on('pointermove', (e) => {
            const p = e.getLocalPosition(world);
            const hx = Math.floor(p.x / TILE);
            const hy = Math.floor(p.y / TILE);
            if (onCellHover) onCellHover(hx, (hx >= 0 && hx < mapData.width && hy >= 0 && hy < mapData.height) ? hy : null);
        });

        if (origin && range !== undefined) {
            const rl = new Graphics();
            const [ox, oy] = origin;
            for (let dy = -range; dy <= range; dy++) {
                for (let dx = -range; dx <= range; dx++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) <= range && (dx !== 0 || dy !== 0)) {
                        const tx = ox + dx, ty = oy + dy;
                        if (tx >= 0 && tx < mapData.width && ty >= 0 && ty < mapData.height) {
                            rl.rect(tx * TILE, ty * TILE, TILE, TILE).fill({ color: 0x22c55e, alpha: 0.1 });
                        }
                    }
                }
            }
            uiLayer.addChild(rl);
        }

    }, [mapData, entities, isReady, range, origin]);

    // 3. Visual Effects Processor
    useEffect(() => {
        if (!isReady || !visualEvents?.length) return;
        const app = appRef.current;
        const world = worldRef.current;
        if (!app || !world) return;

        visualEvents.forEach(evt => {
            if (evt.type === 'FCT') {
                const style = new TextStyle({
                    fontFamily: 'monospace',
                    fontSize: evt.style === 'crit' ? 18 : 14,
                    fontWeight: '900',
                    fill: evt.style === 'crit' ? '#fbbf24' : (evt.style === 'miss' ? '#94a3b8' : '#ef4444'),
                    stroke: { color: '#000000', width: 4 }
                });
                const t = new Text({ text: evt.text, style });
                t.anchor.set(0.5);
                t.x = evt.pos[0] * TILE + TILE / 2;
                t.y = evt.pos[1] * TILE;
                world.addChild(t);

                let elapsed = 0;
                const anim = (ticker: any) => {
                    elapsed += ticker.deltaTime;
                    t.y -= 0.5 * ticker.deltaTime;
                    t.alpha = 1 - (elapsed / 60);
                    if (elapsed > 60) {
                        world.removeChild(t);
                        app.ticker.remove(anim);
                    }
                };
                app.ticker.add(anim);

            } else if (evt.type === 'SHAKE') {
                const ox = world.x, oy = world.y;
                let elapsed = 0;
                const intensity = evt.intensity || 5;
                const anim = (ticker: any) => {
                    elapsed += ticker.deltaTime;
                    world.x = ox + (Math.random() - 0.5) * intensity;
                    world.y = oy + (Math.random() - 0.5) * intensity;
                    if (elapsed > 15) {
                        world.x = ox; world.y = oy;
                        app.ticker.remove(anim);
                    }
                };
                app.ticker.add(anim);

            } else if (evt.type === 'ACTION_START') {
                const group = entGroupRef.current.get(evt.id);
                if (group) {
                    const ring = new Graphics().circle(0, 0, 20).stroke({ color: 0xfbbf24, width: 2, alpha: 0.8 });
                    group.addChild(ring);
                    let elapsed = 0;
                    const anim = (ticker: any) => {
                        elapsed += ticker.deltaTime;
                        ring.scale.set(1 + Math.sin(elapsed * 0.2) * 0.2);
                        if (elapsed > 60) {
                            group.removeChild(ring);
                            app.ticker.remove(anim);
                        }
                    };
                    app.ticker.add(anim);
                }
            }
        });
    }, [visualEvents, isReady]);

    return <div ref={containerRef} className="w-full h-full bg-[#0f0f13] overflow-hidden" />;
}
