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
}

export const useGameStore = create<GameState>((set, get) => ({
    meta: { title: "Initializing...", description: "", turn: 1, world_pos: [500, 500] },
    map: { width: 20, height: 20, grid: [], biome: 'wilderness' },
    entities: [],
    log: ["Tactical Interface initialized."],
    selectedEntityId: null,
    isDMThinking: false,

    loadSession: (data) => set({ ...data }),

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
                        // For the demo, we just apply the move
                        // In reality, we'd find the entity and update its pos
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
                });
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

    equipItem: async (itemId: string, slot: string) => {
        const { dmChat } = get();
        await dmChat(`I want to equip my ${itemId} to my ${slot} slot.`);
    }
}));
