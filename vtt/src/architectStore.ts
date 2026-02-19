import { create } from 'zustand';

export interface ArchitectEntity {
    id: string;
    name: string;
    type: string;
    icon: string;
    pos: [number, number];
    properties: Record<string, any>;
}

interface ArchitectState {
    selectedTool: 'PAINT' | 'SELECT' | 'ENTITY';
    selectedBrush: string | null;
    selectedEntityTemplate: string | null;
    placedEntities: ArchitectEntity[];
    history: any[];

    setTool: (tool: 'PAINT' | 'SELECT' | 'ENTITY') => void;
    setBrush: (brush: string | null) => void;
    setEntityTemplate: (template: string | null) => void;
    addEntity: (entity: ArchitectEntity) => void;
    updateEntity: (id: string, updates: Partial<ArchitectEntity>) => void;
}

export const useArchitectStore = create<ArchitectState>((set) => ({
    selectedTool: 'SELECT',
    selectedBrush: null,
    selectedEntityTemplate: null,
    placedEntities: [],
    history: [],

    setTool: (tool) => set({ selectedTool: tool }),
    setBrush: (brush) => set({ selectedBrush: brush }),
    setEntityTemplate: (template) => set({ selectedEntityTemplate: template }),
    addEntity: (entity) => set((state) => ({ placedEntities: [...state.placedEntities, entity] })),
    updateEntity: (id, updates) => set((state) => ({
        placedEntities: state.placedEntities.map(e => e.id === id ? { ...e, ...updates } : e)
    })),
}));
