import { create } from 'zustand';
import type { SessionData, Position } from './types';

interface GameState extends SessionData {
    loadSession: (data: SessionData) => void;
    moveEntity: (id: string, newPos: Position) => void;
    addLog: (message: string, type?: 'system' | 'dm') => void;
    selectedEntityId: string | null;
    selectEntity: (id: string | null) => void;
    fetchNewSession: (x?: number, y?: number) => Promise<void>;
    submitResult: (outcome: 'VICTORY' | 'DEFEAT') => Promise<void>;
    dmChat: (message: string) => Promise<void>;
    loadPlayerDetailed: (name: string) => Promise<void>;
    equipItem: (itemId: string, slot: string) => Promise<void>;
    isDMThinking: boolean;
    quests: any[];
    fetchQuests: () => Promise<void>;

    // UI Drawer States
    isInventoryOpen: boolean;
    setInventoryOpen: (open: boolean) => void;
    isQuestLogOpen: boolean;
    setQuestLogOpen: (open: boolean) => void;
    syncTacticalState: () => Promise<void>;

    // Architect Mode
    architectGrid: any | null;
    fetchArchitectGrid: () => Promise<void>;
    paintArchitectTile: (x: number, y: number, tileIndex: number, radius?: number) => Promise<void>;
}

export const useGameStore = create<GameState>((set, get) => ({
    meta: { title: "Initializing...", description: "", turn: 1, world_pos: [500, 500] },
    map: { width: 20, height: 20, grid: [], biome: 'wilderness' },
    entities: [],
    log: ["Tactical Interface initialized."],
    selectedEntityId: null,
    isDMThinking: false,
    quests: [],
    isInventoryOpen: false,
    isQuestLogOpen: false,

    loadSession: (data) => set({ ...data }),

    setInventoryOpen: (open) => set({ isInventoryOpen: open }),
    setQuestLogOpen: (open) => set({ isQuestLogOpen: open }),

    moveEntity: (id, [x, y]) => set((state) => ({
        entities: state.entities.map(e =>
            e.id === id ? { ...e, pos: [x, y] } : e
        )
    })),

    addLog: (msg, type = 'system') => set((state) => ({
        log: [...state.log, type === 'dm' ? `[THE ORACLE] ${msg}` : `[T${state.meta.turn}] ${msg}`]
    })),

    selectEntity: (id) => set({ selectedEntityId: id }),

    fetchNewSession: async (x = 500, y = 500) => {
        try {
            const response = await fetch(`/api/tactical/generate?x=${x}&y=${y}`);
            if (!response.ok) throw new Error('Failed to fetch session');
            const data = await response.json();
            set({ ...data, selectedEntityId: null });
            set((state) => ({ log: [...state.log, `[SYSTEM] Battle Map Loaded: ${data.meta.title}`] }));

            // Auto-load detailed stats for Burt
            const { loadPlayerDetailed } = get();
            await loadPlayerDetailed("Burt");
        } catch (e) {
            console.error("Brain Server is offline!", e);
            set((state) => ({ log: [...state.log, "[ERROR] Brain Server is offline!"] }));
        }
    },

    dmChat: async (message: string) => {
        const { entities, meta } = get();
        set({ isDMThinking: true });

        try {
            const response = await fetch('/api/dm/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    context: {
                        world_pos: meta.world_pos,
                        player: entities.find(e => e.type === 'player') || {},
                        entities: entities.map(e => ({ id: e.id, name: e.name, hp: e.hp, pos: e.pos }))
                    }
                })
            });

            if (!response.ok) throw new Error("DM Service Error");

            const data = await response.json();

            // 1. Log the narrative
            set((state) => ({
                log: [...state.log, `[THE ORACLE] ${data.narrative}`],
                isDMThinking: false
            }));

            // 2. Process Visual Updates
            if (data.visual_updates && Array.isArray(data.visual_updates)) {
                data.visual_updates.forEach((update: any) => {
                    if (update.type === 'MOVE_TOKEN') {
                        set((state) => ({
                            entities: state.entities.map(e =>
                                (e.id === update.id || e.name === update.id) ? { ...e, pos: update.pos } : e
                            )
                        }));
                    }
                    if (update.type === 'UPDATE_HP') {
                        set((state) => ({
                            entities: state.entities.map(e =>
                                (e.id === update.id || e.name === update.id) ? { ...e, hp: update.hp } : e
                            )
                        }));
                    }
                    if (update.type === 'ADD_ITEM') {
                        set((state) => ({
                            entities: state.entities.map(e =>
                                e.type === 'player' ? {
                                    ...e,
                                    inventory: [...(e.inventory || []), update.item]
                                } : e
                            )
                        }));
                        set((state) => ({ log: [...state.log, `[LOOT] Found item: ${update.item.Name}`] }));
                    }
                    if (update.type === 'OPEN_INVENTORY') {
                        set({ isInventoryOpen: true });
                    }
                });
            }

            // Sync quests if quest updates happened
            if (data.mechanical_log.includes("Success") || data.mechanical_log.includes("You searched")) {
                const { fetchQuests } = get();
                fetchQuests();
            }

        } catch (e) {
            console.error("AI DM Interaction failed", e);
            set({ isDMThinking: false });
        }
    },

    submitResult: async (outcome) => {
        const { entities, meta } = get();
        const deadEnemies = entities.filter(e => e.hp <= 0 && e.type === 'enemy').map(e => e.id);

        try {
            const response = await fetch('/api/tactical/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    outcome,
                    enemies_killed: deadEnemies,
                    loot_taken: [],
                    x: meta.world_pos[0],
                    y: meta.world_pos[1]
                })
            });
            const data = await response.json();
            set((state) => ({ log: [...state.log, `[REPORT] ${data.message}`] }));
        } catch (e) {
            console.error("Failed to submit result", e);
        }
    },

    loadPlayerDetailed: async (name: string) => {
        try {
            const response = await fetch(`/api/char/${name}`);
            if (!response.ok) throw new Error('Failed to fetch player');
            const data = await response.json();

            // Normalize SAGA Brain data to VTT types
            const normalized = {
                ...data,
                hp: data.HP || data.hp || 0,
                maxHp: data.maxHp || data.maxHP || data.HP || 100,
                sp: data.SP || data.sp || data.Stamina || 0,
                maxSp: data.maxSp || data.maxSP || data.SP || data.Stamina || 0,
                fp: data.FP || data.fp || data.Focus || 0,
                maxFp: data.maxFp || data.maxFP || data.FP || data.Focus || 0,
                stats: data.Stats || data.stats || {},
                inventory: data.Inventory || data.inventory || [],
                equipped: data.Equipped || data.equipped || {}
            };

            set((state) => ({
                entities: state.entities.map(e =>
                    e.type === 'player' ? { ...e, ...normalized } : e
                )
            }));
        } catch (e) {
            console.error("Failed to load detailed player stats", e);
        }
    },

    fetchQuests: async () => {
        try {
            const response = await fetch('/api/campaign/quests');
            if (!response.ok) throw new Error('Failed to fetch quests');
            const data = await response.json();
            set({ quests: data });
        } catch (e) {
            console.error("Failed to fetch quests", e);
        }
    },

    equipItem: async (itemId: string, slot: string) => {
        const { dmChat } = get();
        await dmChat(`I want to equip my ${itemId} to my ${slot} slot.`);
    },

    syncTacticalState: async () => {
        try {
            const response = await fetch('/api/tactical/state');
            if (response.status === 404) return; // No active combat
            if (!response.ok) throw new Error('State fetch failed');

            const data = await response.json();

            // Map TacticalStateResponse to SessionData
            set((state) => ({
                round: data.round,
                turn_order: data.turn_order,
                active_combatant: data.active_combatant,
                entities: state.entities.map(e => {
                    if (e.type === 'player' && e.name === data.player_stats.name) {
                        return {
                            ...e,
                            hp: data.player_stats.health.current,
                            pos: [data.player_stats.coordinates.x, data.player_stats.coordinates.y],
                            stats: data.player_stats.attributes
                        };
                    }
                    const enemy = data.enemy_list.find((en: any) => en.id === e.id);
                    if (enemy) {
                        return {
                            ...e,
                            hp: enemy.health.current,
                            pos: [enemy.coordinates.x, enemy.coordinates.y]
                        };
                    }
                    return e;
                })
            }));
        } catch (e) {
            console.error("Failed to sync tactical state", e);
        }
    },

    architectGrid: null,
    fetchArchitectGrid: async () => {
        try {
            const res = await fetch('/api/architect/grid');
            if (!res.ok) throw new Error('Grid load failed');
            const data = await res.json();
            set({ architectGrid: data });
        } catch (e) {
            console.error(e);
        }
    },

    paintArchitectTile: async (x, y, tileIndex, radius = 2) => {
        const { architectGrid } = get();
        if (!architectGrid) return;

        // Optimistic Update
        const newGrid = [...architectGrid.grid];
        const r_sq = radius * radius;
        for (let dy = -radius; dy <= radius; dy++) {
            for (let dx = -radius; dx <= radius; dx++) {
                if (dx * dx + dy * dy <= r_sq) {
                    const nx = x + dx;
                    const ny = y + dy;
                    if (nx >= 0 && nx < architectGrid.width && ny >= 0 && ny < architectGrid.height) {
                        newGrid[ny] = [...newGrid[ny]];
                        newGrid[ny][nx] = tileIndex;
                    }
                }
            }
        }
        set({ architectGrid: { ...architectGrid, grid: newGrid } });

        try {
            await fetch('/api/architect/paint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y, tile_index: tileIndex, radius })
            });
        } catch (e) {
            console.error("Paint failed on server", e);
        }
    }
}));
