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
    selectedTool: 'PAINT' | 'SELECT' | 'ENTITY' | 'SCATTER' | 'CLIMATE';
    selectedBrush: string | null;
    brushRadius: number;
    selectedEntityTemplate: string | null;
    scatterSettings: { radius: number; density: number; template: string | null };

    // Phase 6 UI States
    viewLayer: 'GLOBAL' | 'REGIONAL' | 'LOCAL' | 'TACTICAL';
    climateSettings: { min_temp: number; max_temp: number; wind_intensity: number };
    selectedPlacedEntityId: string | null;

    placedEntities: ArchitectEntity[];
    history: any[];

    setTool: (tool: 'PAINT' | 'SELECT' | 'ENTITY' | 'SCATTER' | 'CLIMATE') => void;
    setBrush: (brush: string | null) => void;
    setBrushRadius: (radius: number) => void;
    setEntityTemplate: (template: string | null) => void;
    setScatterSettings: (settings: Partial<{ radius: number; density: number; template: string | null }>) => void;

    setViewLayer: (layer: 'GLOBAL' | 'REGIONAL' | 'LOCAL' | 'TACTICAL') => void;
    setClimateSettings: (settings: Partial<{ min_temp: number; max_temp: number; wind_intensity: number }>) => void;
    setSelectedPlacedEntity: (id: string | null) => void;

    // Phase 7 Assets
    definedAssets: {
        species: any[];
        factions: any[];
        resources: any[];
        wildlife: any[];
        flora: any[];
    };
    isAssetEditorOpen: boolean;
    setAssetEditorOpen: (open: boolean) => void;
    fetchAssets: () => Promise<void>;
    saveAsset: (category: string, data: any) => Promise<void>;

    addEntity: (entity: ArchitectEntity) => void;
    updateEntity: (id: string, updates: Partial<ArchitectEntity>) => void;
}

export const useArchitectStore = create<ArchitectState>((set) => ({
    selectedTool: 'SELECT',
    selectedBrush: null,
    brushRadius: 2,
    selectedEntityTemplate: null,
    scatterSettings: { radius: 3, density: 0.2, template: null },

    // Phase 6 UI States Defaults
    viewLayer: 'TACTICAL',
    climateSettings: { min_temp: -10, max_temp: 35, wind_intensity: 0.5 },
    selectedPlacedEntityId: null,

    placedEntities: [],
    history: [],

    setTool: (tool) => set({ selectedTool: tool }),
    setBrush: (brush) => set({ selectedBrush: brush }),
    setBrushRadius: (r) => set({ brushRadius: r }),
    setEntityTemplate: (template) => set({ selectedEntityTemplate: template }),
    setScatterSettings: (settings) => set((state) => ({ scatterSettings: { ...state.scatterSettings, ...settings } })),

    setViewLayer: (layer) => set({ viewLayer: layer }),
    setClimateSettings: (settings) => set((state) => ({ climateSettings: { ...state.climateSettings, ...settings } })),
    setSelectedPlacedEntity: (id) => set({ selectedPlacedEntityId: id }),

    definedAssets: {
        species: [], factions: [], resources: [], wildlife: [], flora: []
    },
    isAssetEditorOpen: false,
    setAssetEditorOpen: (open) => set({ isAssetEditorOpen: open }),

    fetchAssets: async () => {
        try {
            const res = await fetch("http://localhost:8000/architect/assets");
            if (res.ok) {
                const data = await res.json();
                set({ definedAssets: data });
            }
        } catch (e) {
            console.error("Failed to fetch architect assets:", e);
        }
    },

    saveAsset: async (category, data) => {
        try {
            const res = await fetch("http://localhost:8000/architect/assets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ category, data })
            });
            if (res.ok) {
                // Refresh local state list
                const store = useArchitectStore.getState();
                await store.fetchAssets();
            }
        } catch (e) {
            console.error("Failed to save asset:", e);
        }
    },

    addEntity: (entity) => set((state) => ({ placedEntities: [...state.placedEntities, entity] })),
    updateEntity: (id, updates) => set((state) => ({
        placedEntities: state.placedEntities.map(e => e.id === id ? { ...e, ...updates } : e)
    })),
}));
