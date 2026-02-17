export type Position = [number, number]; // [x, y] on tactical grid

export interface Entity {
    id: string;
    name: string;
    type: 'player' | 'enemy' | 'npc';
    pos: Position;
    hp: number;
    maxHp: number;
    sp?: number;
    maxSp?: number;
    fp?: number;
    maxFp?: number;
    cmp?: number;
    maxCmp?: number;
    icon: string;
    tags: string[];
    stats?: Record<string, number>;
    inventory?: string[];
    equipped?: Record<string, string | null>;
}

export interface MapData {
    width: number;
    height: number;
    grid: number[][]; // 0 = floor, 1 = wall
    biome: 'forest' | 'dungeon' | 'wilderness';
}

export interface SessionData {
    meta: {
        title: string;
        description: string;
        turn: number;
        world_pos: [number, number];
    };
    map: MapData;
    entities: Entity[];
    log: string[];
    round?: number;
    turn_order?: string[];
    active_combatant?: string | null;
}

export interface QuestObjective {
    description: string;
    slug: string;
    target_count: number;
    current_count: number;
    is_complete: boolean;
}

export interface Quest {
    id: string;
    title: string;
    description: string;
    status: 'ACTIVE' | 'COMPLETED' | 'FAILED';
    objectives: QuestObjective[];
    rewards: {
        gold: number;
        xp: number;
        items: string[];
    };
    narrative_hook: string;
}
