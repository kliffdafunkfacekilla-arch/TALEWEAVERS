import { useEffect, useRef, useState, useMemo } from 'react';
import { Application, Container, Graphics, Assets, Sprite, Texture, Rectangle, Point, Text, TextStyle } from 'pixi.js';
import { clsx } from 'clsx';

interface MapCanvasProps {
    mapData: any;
    entities: any[];
    onCellClick: (x: number, y: number) => void;
    onCellHover?: (x: number, y: number | null) => void;
    range?: number;
    aoeRadius?: number;
    origin?: [number, number];
    visualEvents?: any[]; // Transient events like [{type: 'FCT', ...}]
}

const SHEET_CONFIG = {
    url: '/spritesheet.png',
    spriteWidth: 32,
    spriteHeight: 32,
};

export function MapCanvas({ mapData, entities, onCellClick, onCellHover, range, aoeRadius, origin, visualEvents }: MapCanvasProps) {
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

                // Elevation adjustment
                const height = mapData.elevation?.[`${x},${y}`] || 0;
                if (height > 0) {
                    tile.tint = height === 1 ? 0xcccccc : 0x999999; // Darker the higher? No, brighter or distinct.
                    // Let's go with brighter for high ground
                    tile.tint = height === 1 ? 0xffffff : 0xeeeeee;
                    // Actually, let's use a scale
                }
                tile.x = x * TILE; tile.y = y * TILE;
                bgLayer.addChild(tile);

                if (height > 0) {
                    const hText = new Text({ text: `${height}`, style: { fontSize: 8, fill: 0xffffff, alpha: 0.5 } });
                    hText.x = x * TILE + 2; hText.y = y * TILE + 2;
                    bgLayer.addChild(hText);
                }

                const hazard = mapData.terrain?.[`${x},${y}`];
                if (hazard) {
                    const hColor = hazard === 'ACID' ? 0x84cc16 : (hazard === 'LAVA' ? 0xef4444 : (hazard === 'GOO' ? 0xa855f7 : (hazard === 'WOODEN_BRIDGE' ? 0x78350f : 0x64748b)));
                    const hAlpha = (hazard === 'GOO' || hazard === 'WOODEN_BRIDGE') ? 0.6 : 0.3;
                    const overlay = new Graphics().rect(0, 0, TILE, TILE).fill({ color: hColor, alpha: hAlpha });

                    if (hazard === 'STEAM_VENT') {
                        overlay.stroke({ color: 0x1e293b, width: 2, alpha: 0.8 });
                        // Add central 'grate' lines
                        overlay.moveTo(TILE * 0.2, TILE * 0.2).lineTo(TILE * 0.8, TILE * 0.8).stroke({ color: 0x1e293b, width: 1 });
                        overlay.moveTo(TILE * 0.8, TILE * 0.2).lineTo(TILE * 0.2, TILE * 0.8).stroke({ color: 0x1e293b, width: 1 });
                    }

                    if (hazard === 'WOODEN_BRIDGE') {
                        overlay.stroke({ color: 0x451a03, width: 2, alpha: 0.8 });
                        // Add horizontal plank lines
                        for (let i = 1; i < 4; i++) {
                            overlay.moveTo(2, TILE * (i / 4)).lineTo(TILE - 2, TILE * (i / 4)).stroke({ color: 0x451a03, width: 1, alpha: 0.6 });
                        }
                    }

                    overlay.x = x * TILE; overlay.y = y * TILE;
                    bgLayer.addChild(overlay);
                }

                const item = mapData.items?.[`${x},${y}`];
                if (item) {
                    const iColor = item === 'MIGHT_VIAL' ? 0xf59e0b : (item === 'SPEED_VIAL' ? 0x3b82f6 : 0xec4899);
                    const vial = new Graphics().circle(TILE / 2, TILE / 2, 6).fill(iColor).circle(TILE / 2, TILE / 2, 10).stroke({ color: iColor, alpha: 0.3, width: 2 });
                    vial.x = x * TILE; vial.y = y * TILE;
                    bgLayer.addChild(vial);
                }
            });
        });

        // Entities
        entGroupRef.current.clear();
        entities.forEach(ent => {
            const eGroup = new Container();
            const sheetMatch = ent.icon?.match(/sheet:(\d+)/);
            const isBoss = ent.tags?.includes('boss');
            const scale = isBoss ? 1.2 : 0.8;

            if (tex) {
                const s = new Sprite(tex);
                s.anchor.set(0.5);
                s.width = TILE * scale; s.height = TILE * scale;
                eGroup.addChild(s);
            }

            if (isBoss) {
                const bossGlow = new Graphics().circle(0, 0, TILE * 0.6).fill({ color: 0xfbbf24, alpha: 0.15 }).stroke({ color: 0xfbbf24, alpha: 0.3, width: 2 });
                eGroup.addChildAt(bossGlow, 0);
            }

            eGroup.x = ent.pos[0] * TILE + TILE / 2;
            eGroup.y = ent.pos[1] * TILE + TILE / 2;

            if (ent.hp !== undefined) {
                const hpBar = new Graphics().rect(-15, 18, 30, 4).fill(0x333333).rect(-15, 18, 30 * (ent.hp / (ent.maxHp || 100)), 4).fill(0x22c55e);
                eGroup.addChild(hpBar);
            }

            if (ent.statusEffects && ent.statusEffects.length > 0) {
                ent.statusEffects.forEach((eff: any, i: number) => {
                    const eColor = eff.type === 'POISON' ? 0x84cc16 : 0xf97316;
                    const dot = new Graphics().circle(-15 + (i * 6), 25, 2).fill(eColor);
                    eGroup.addChild(dot);
                });
            }

            if (ent.tempBuffs && ent.tempBuffs.length > 0) {
                const aura = new Graphics().circle(0, 0, TILE * 0.45).stroke({ color: 0xf59e0b, alpha: 0.5, width: 2 });
                eGroup.addChildAt(aura, 0); // Put behind the sprite
            }

            // Fury Aura (ENRAGED)
            if (ent.statusEffects && ent.statusEffects.some((s: any) => s.type === 'ENRAGED')) {
                const furyAura = new Graphics().circle(0, 0, TILE * 0.48).stroke({ color: 0xef4444, alpha: 0.7, width: 3 });
                eGroup.addChildAt(furyAura, 0);
            }

            // Adaptive Shell Visual (Any RESIST_ status)
            if (ent.statusEffects && ent.statusEffects.some((s: any) => s.type.startsWith('RESIST_'))) {
                const shell = new Graphics()
                    .poly([
                        0, -TILE * 0.5,
                        TILE * 0.45, -TILE * 0.25,
                        TILE * 0.45, TILE * 0.25,
                        0, TILE * 0.5,
                        -TILE * 0.45, TILE * 0.25,
                        -TILE * 0.45, -TILE * 0.25
                    ])
                    .stroke({ color: 0x22d3ee, alpha: 0.6, width: 2 });
                eGroup.addChildAt(shell, 0);
            }

            // Pheromone Aura (Pack Leader)
            if (ent.metadata?.Traits?.["Pheromone Synthesis"]) {
                const pheromoneAura = new Graphics().circle(0, 0, TILE * 3).fill({ color: 0x22c55e, alpha: 0.1 });
                eGroup.addChildAt(pheromoneAura, 0);
            }

            // Pheromone Buff Indicator
            if (ent.statusEffects && ent.statusEffects.some((s: any) => s.type === 'PHEROMONES')) {
                const buffIndicator = new Graphics().circle(TILE * 0.35, -TILE * 0.35, TILE * 0.1).fill(0x22c55e);
                eGroup.addChild(buffIndicator);
            }

            // Symbiotic Tether
            if (ent.symbioticLink && ent.hp > 0) {
                const partner = mapData.entities.find((e: any) => e.id === ent.symbioticLink);
                if (partner && partner.hp > 0 && ent.id < partner.id) { // Draw once
                    const tether = new Graphics()
                        .moveTo(0, 0)
                        .lineTo((partner.pos[0] - ent.pos[0]) * TILE, (partner.pos[1] - ent.pos[1]) * TILE)
                        .stroke({ color: 0xec4899, width: 2, alpha: 0.6 });
                    eGroup.addChildAt(tether, 0);
                }
            }

            // Aggro indicator
            const threatMap = mapData.threat || {};
            let isAggroed = false;
            Object.keys(threatMap).forEach(npcId => {
                const npcThreats = threatMap[npcId];
                if (!npcThreats || Object.keys(npcThreats).length === 0) return;
                const highestThreatId = Object.keys(npcThreats).reduce((a, b) => npcThreats[a] > npcThreats[b] ? a : b);
                if (highestThreatId === ent.id) isAggroed = true;
            });

            if (isAggroed) {
                const threatRing = new Graphics().circle(0, 0, TILE * 0.52).stroke({ color: 0xef4444, alpha: 0.4, width: 3 });
                eGroup.addChildAt(threatRing, 0);
            }

            // Cover indicator
            const charTerrain = mapData.terrain?.[`${ent.pos[0]},${ent.pos[1]}`];
            if (charTerrain === 'DIFFICULT') {
                const shield = new Graphics().poly([-4, -22, 4, -22, 0, -18]).fill(0x60a5fa);
                eGroup.addChild(shield);
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

        // AoE Template Overlay
        if (mapData.hoveredX !== undefined && mapData.hoveredY !== undefined && aoeRadius !== undefined) {
            const hx = mapData.hoveredX;
            const hy = mapData.hoveredY;
            const aoeOver = new Graphics();
            for (let dy = -aoeRadius; dy <= aoeRadius; dy++) {
                for (let dx = -aoeRadius; dx <= aoeRadius; dx++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) <= aoeRadius) {
                        const tx = hx + dx;
                        const ty = hy + dy;
                        if (tx >= 0 && tx < mapData.width && ty >= 0 && ty < mapData.height) {
                            aoeOver.rect(tx * TILE, ty * TILE, TILE, TILE).fill({ color: 0xef4444, alpha: 0.3 });
                        }
                    }
                }
            }
            uiLayer.addChild(aoeOver);
        }

        // Hover Overlay (Pixi-side)
        if (mapData.hoveredEntity && isReady) {
            const ent = mapData.hoveredEntity;
            const style = new TextStyle({ fontSize: 10, fill: 0xffffff, fontWeight: 'bold' });

            let hoverLines: string[] = [];
            if (ent.status && ent.status.length > 0) {
                ent.status.forEach((s: any) => hoverLines.push(`${s.type} (${s.duration || 1})`));
            }
            if (ent.buffs && ent.buffs.length > 0) {
                ent.buffs.forEach((b: any) => hoverLines.push(`${b.type} (${b.duration || 1})`));
            }

            if (hoverLines.length === 0) {
                const res = ent.status?.find((s: any) => s.type.startsWith('RESIST_'))?.type?.replace('RESIST_', '') || 'NONE';
                hoverLines.push(`HARDENED: ${res}`);
            }

            const hoverText = hoverLines.join('\n');
            const info = new Text({ text: hoverText, style });

            const tooltip = new Graphics()
                .rect(0, 0, Math.max(80, info.width + 10), Math.max(20, info.height + 10))
                .fill({ color: 0x000000, alpha: 0.8 })
                .stroke({ color: 0xffffff, alpha: 0.2, width: 1 });

            tooltip.x = ent.pos[0] * TILE + TILE;
            tooltip.y = ent.pos[1] * TILE - (info.height + 10);

            info.x = 5; info.y = 5;
            tooltip.addChild(info);
            uiLayer.addChild(tooltip);
        }

    }, [mapData, entities, isReady, range, origin, aoeRadius]);

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
                    fill: evt.style === 'crit' ? '#fbbf24' : (evt.style === 'miss' ? '#94a3b8' : (evt.style === 'react' ? '#22d3ee' : '#ef4444')),
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
            } else if (evt.type === 'PROJECTILE') {
                const dot = new Graphics().circle(0, 0, 4).fill(evt.color || '#ffffff');
                dot.x = evt.from[0] * TILE + TILE / 2;
                dot.y = evt.from[1] * TILE + TILE / 2;
                world.addChild(dot);

                const tx = evt.to[0] * TILE + TILE / 2;
                const ty = evt.to[1] * TILE + TILE / 2;
                const dx = tx - dot.x;
                const dy = ty - dot.y;

                let elapsed = 0;
                const anim = (ticker: any) => {
                    elapsed += ticker.deltaTime;
                    dot.x += dx * 0.1 * ticker.deltaTime;
                    dot.y += dy * 0.1 * ticker.deltaTime;
                    if (Math.abs(dot.x - tx) < 5 && Math.abs(dot.y - ty) < 5) {
                        world.removeChild(dot);
                        app.ticker.remove(anim);
                    }
                };
                app.ticker.add(anim);

            } else if (evt.type === 'AOE_PULSE') {
                const px = evt.pos[0] * TILE + TILE / 2;
                const py = evt.pos[1] * TILE + TILE / 2;
                const ring = new Graphics().circle(0, 0, TILE * (evt.radius || 1)).stroke({ color: evt.color || '#ffffff', width: 2, alpha: 0.5 });
                ring.x = px;
                ring.y = py;
                ring.scale.set(0);
                world.addChild(ring);

                let elapsed = 0;
                const anim = (ticker: any) => {
                    elapsed += ticker.deltaTime;
                    ring.scale.set(elapsed / 30);
                    ring.alpha = 1 - (elapsed / 30);
                    if (elapsed > 30) {
                        world.removeChild(ring);
                        app.ticker.remove(anim);
                    }
                };
                app.ticker.add(anim);
            } else if (evt.type === 'JUMP') {
                const px1 = evt.from[0] * TILE + TILE / 2;
                const py1 = evt.from[1] * TILE + TILE / 2;
                const px2 = evt.to[0] * TILE + TILE / 2;
                const py2 = evt.to[1] * TILE + TILE / 2;

                const arc = new Graphics();
                arc.moveTo(px1, py1);

                // Control point for parabola
                const cx = (px1 + px2) / 2;
                const cy = Math.min(py1, py2) - TILE * 2;

                arc.quadraticCurveTo(cx, cy, px2, py2);
                arc.stroke({ color: 0xffffff, width: 2, alpha: 0.8 });
                world.addChild(arc);

                let elapsed = 0;
                const anim = (ticker: any) => {
                    elapsed += ticker.deltaTime;
                    arc.alpha = 1 - (elapsed / 45);
                    if (elapsed > 45) {
                        world.removeChild(arc);
                        app.ticker.remove(anim);
                    }
                };
                app.ticker.add(anim);
            }
        });
    }, [visualEvents, isReady]);

    return <div ref={containerRef} className="w-full h-full bg-[#0f0f13] overflow-hidden" />;
}
