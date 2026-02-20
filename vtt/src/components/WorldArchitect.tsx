import { useEffect, useState } from 'react';
import { MapCanvas } from './MapCanvas';
import { AssetEditor } from './AssetEditor';
import { useArchitectStore, ArchitectEntity } from '../architectStore';
import {
    MousePointer2,
    Paintbrush,
    Box,
    Save,
    Play,
    Settings,
    Plus,
    Trash2,
    ChevronRight,
    Layers,
    Cpu,
    History,
    RefreshCw,
    Sparkles,
    CloudRain
} from 'lucide-react';
import { clsx } from 'clsx';
import { useGameStore } from '../store';

export function WorldArchitect() {
    const { map, entities, syncTacticalState, architectGrid, fetchArchitectGrid, paintArchitectTile } = useGameStore();
    const {
        selectedTool, setTool,
        selectedBrush, setBrush,
        brushRadius, setBrushRadius,
        placedEntities, addEntity,
        selectedEntityTemplate, setEntityTemplate,
        scatterSettings, setScatterSettings,
        viewLayer, setViewLayer,
        climateSettings, setClimateSettings,
        setAssetEditorOpen
    } = useArchitectStore();

    const [inspectorId, setInspectorId] = useState<string | null>(null);
    const [currentYear, setCurrentYear] = useState(1);
    const [availableYears, setAvailableYears] = useState<number[]>([]);

    useEffect(() => {
        fetchArchitectGrid();

        // Fetch available history years on mount
        fetch("http://localhost:8000/architect/history/list")
            .then(res => res.json())
            .then(data => {
                if (data.years && data.years.length > 0) {
                    setAvailableYears(data.years);
                    setCurrentYear(data.years[data.years.length - 1]);
                }
            });
    }, []);

    const handleTimelineScrub = async (year: number) => {
        setCurrentYear(year);
        try {
            const res = await fetch(`http://localhost:8000/architect/history/load/${year}`, { method: "POST" });
            if (res.ok) {
                // Success: The ECS has been updated on the backend.
                // We need to trigger a refresh of the frontend entity list.
                syncTacticalState();
            }
        } catch (e) {
            console.error("Scrub failed:", e);
        }
    };

    const templates = [
        { id: 'orc', name: 'Orc Tribe', icon: 'sheet:5076', type: 'Faction' },
        { id: 'human', name: 'Human Settlement', icon: 'sheet:3', type: 'Location' },
        { id: 'dungeon', name: 'Ancient Ruin', icon: 'sheet:2', type: 'Location' },
        { id: 'beast', name: 'Ash Bison', icon: 'sheet:5074', type: 'Fauna' },
    ];

    const brushes = [
        { id: 'mountain', name: 'Mountain', color: '#4b5563', index: 896 },
        { id: 'water', name: 'Water', color: '#2563eb', index: 194 },
        { id: 'forest', name: 'Forest', color: '#16a34a', index: 130 },
        { id: 'grass', name: 'Grass', color: '#166534', index: 128 },
    ];

    const handlePaint = (x: number, y: number) => {
        if (selectedTool === 'PAINT' && selectedBrush) {
            const brush = brushes.find(b => b.id === selectedBrush);
            if (brush) {
                paintArchitectTile(x, y, brush.index, brushRadius);
            }
        }
    };

    const handleCanvasClick = (x: number, y: number) => {
        if (selectedTool === 'ENTITY' && selectedEntityTemplate) {
            const template = templates.find(t => t.id === selectedEntityTemplate);
            if (template) {
                const newEnt: ArchitectEntity = {
                    id: `ent_${Date.now()}`,
                    name: template.name,
                    type: template.type,
                    icon: template.icon,
                    pos: [x, y],
                    properties: {
                        population: 100,
                        aggression: 0.5,
                        expansion: 0.5
                    }
                };
                addEntity(newEnt);
            }
        } else if (selectedTool === 'SCATTER' && scatterSettings.template) {
            const template = templates.find(t => t.id === scatterSettings.template);
            if (template) {
                const radius = scatterSettings.radius;
                const count = Math.floor((Math.PI * radius * radius) * scatterSettings.density);
                for (let i = 0; i < count; i++) {
                    const angle = Math.random() * Math.PI * 2;
                    const r = Math.sqrt(Math.random()) * radius;
                    const offsetX = Math.round(Math.cos(angle) * r);
                    const offsetY = Math.round(Math.sin(angle) * r);
                    const newEnt: ArchitectEntity = {
                        id: `ent_sct_${Date.now()}_${i}`,
                        name: `${template.name} (${Math.random().toString(36).substring(7)})`,
                        type: template.type,
                        icon: template.icon,
                        pos: [x + offsetX, y + offsetY],
                        properties: {
                            population: 10,
                            aggression: Math.random(),
                            expansion: Math.random()
                        }
                    };
                    addEntity(newEnt);
                }
            }
        } else if (selectedTool === 'PAINT') {
            handlePaint(x, y);
        }
    };

    return (
        <div className="flex w-full h-full bg-[#050508] text-slate-300 overflow-hidden">
            {/* LEFT: TOOLBAR & PALETTE */}
            <div className="w-72 border-r border-white/5 bg-[#0a0a0f]/80 backdrop-blur-3xl flex flex-col shadow-2xl z-20">
                <div className="p-6 border-b border-white/5">
                    <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-yellow-500 mb-6 flex items-center gap-2">
                        <Cpu size={14} /> Architect Editor
                    </h2>

                    <div className="flex gap-2 mb-8">
                        {[
                            { id: 'SELECT', icon: MousePointer2 },
                            { id: 'PAINT', icon: Paintbrush },
                            { id: 'ENTITY', icon: Box },
                            { id: 'SCATTER', icon: Sparkles },
                            { id: 'CLIMATE', icon: CloudRain }
                        ].map(tool => (
                            <button
                                key={tool.id}
                                onClick={() => setTool(tool.id as any)}
                                className={clsx(
                                    "p-3 rounded-xl transition-all border",
                                    selectedTool === tool.id
                                        ? "bg-yellow-500/10 border-yellow-500/40 text-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.15)]"
                                        : "bg-white/5 border-white/5 text-slate-500 hover:text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <tool.icon size={20} />
                            </button>
                        ))}
                    </div>

                    {selectedTool === 'PAINT' && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-left-2 transition-all">
                            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Landscape Brushes</p>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-yellow-500 uppercase">Brush Radius</label>
                                <input
                                    type="range" min="1" max="10"
                                    value={brushRadius}
                                    onChange={(e) => setBrushRadius(parseInt(e.target.value))}
                                    className="w-full accent-yellow-500 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{brushRadius} tiles</div>
                            </div>

                            <div className="grid grid-cols-1 gap-2">
                                {brushes.map(brush => (
                                    <button
                                        key={brush.id}
                                        onClick={() => setBrush(brush.id)}
                                        className={clsx(
                                            "flex items-center gap-3 p-3 rounded-xl border transition-all text-xs font-bold",
                                            selectedBrush === brush.id
                                                ? "bg-yellow-500/5 border-yellow-500/20 text-yellow-500"
                                                : "bg-white/5 border-white/5 text-slate-400 hover:bg-white/10"
                                        )}
                                    >
                                        <div className="w-3 h-3 rounded-full shadow-inner" style={{ backgroundColor: brush.color }} />
                                        {brush.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {selectedTool === 'ENTITY' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-left-2 transition-all">
                            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Entity Palette</p>
                            <div className="grid grid-cols-2 gap-2">
                                {templates.map(tmpl => (
                                    <button
                                        key={tmpl.id}
                                        onClick={() => setEntityTemplate(tmpl.id)}
                                        className={clsx(
                                            "flex flex-col items-center gap-2 p-3 rounded-xl border transition-all text-[10px] font-black uppercase text-center",
                                            selectedEntityTemplate === tmpl.id
                                                ? "bg-yellow-500/10 border-yellow-500/40 text-yellow-500"
                                                : "bg-white/5 border-white/5 text-slate-400 hover:bg-white/10"
                                        )}
                                    >
                                        <div className="w-10 h-10 bg-black/40 rounded-lg flex items-center justify-center border border-white/5 group-hover:border-yellow-500/20">
                                            <span className="text-xl">👾</span>
                                        </div>
                                        {tmpl.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {selectedTool === 'SCATTER' && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-left-2 transition-all">
                            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Procedural Scatter</p>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-yellow-500 uppercase">Brush Radius</label>
                                <input
                                    type="range" min="1" max="10"
                                    value={scatterSettings.radius}
                                    onChange={(e) => setScatterSettings({ radius: parseInt(e.target.value) })}
                                    className="w-full accent-yellow-500 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{scatterSettings.radius} tiles</div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-yellow-500 uppercase">Density</label>
                                <input
                                    type="range" min="0.05" max="0.8" step="0.05"
                                    value={scatterSettings.density}
                                    onChange={(e) => setScatterSettings({ density: parseFloat(e.target.value) })}
                                    className="w-full accent-cyan-500 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{Math.round(scatterSettings.density * 100)}%</div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-yellow-500 uppercase">Subject</label>
                                <select
                                    className="w-full bg-white/5 border border-white/10 p-2 rounded-lg text-xs"
                                    value={scatterSettings.template || ''}
                                    onChange={(e) => setScatterSettings({ template: e.target.value })}
                                >
                                    <option value="" disabled>Select subject...</option>
                                    {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                </select>
                            </div>
                        </div>
                    )}

                    {selectedTool === 'CLIMATE' && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-left-2 transition-all">
                            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Global Climate</p>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-orange-500 uppercase">Max Temperature</label>
                                <input
                                    type="range" min="0" max="60"
                                    value={climateSettings.max_temp}
                                    onChange={(e) => setClimateSettings({ max_temp: parseInt(e.target.value) })}
                                    className="w-full accent-orange-500 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{climateSettings.max_temp}°C</div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-cyan-500 uppercase">Min Temperature</label>
                                <input
                                    type="range" min="-40" max="20"
                                    value={climateSettings.min_temp}
                                    onChange={(e) => setClimateSettings({ min_temp: parseInt(e.target.value) })}
                                    className="w-full accent-cyan-500 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{climateSettings.min_temp}°C</div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold text-slate-300 uppercase">Wind Intensity</label>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={climateSettings.wind_intensity}
                                    onChange={(e) => setClimateSettings({ wind_intensity: parseFloat(e.target.value) })}
                                    className="w-full accent-slate-300 bg-white/10"
                                />
                                <div className="text-xs text-right opacity-50">{Math.round(climateSettings.wind_intensity * 100)}%</div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex-grow p-6 overflow-y-auto space-y-2">
                    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-4">World Entities</p>
                    {placedEntities.map(ent => (
                        <div
                            key={ent.id}
                            onClick={() => setInspectorId(ent.id)}
                            className={clsx(
                                "group flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer",
                                inspectorId === ent.id ? "bg-white/10 border-white/20" : "bg-white/5 border-white/5 hover:border-white/10"
                            )}
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-1 px-2 bg-yellow-500/10 rounded text-[9px] font-bold text-yellow-500 tracking-tighter uppercase whitespace-nowrap">
                                    {ent.type}
                                </div>
                                <div className="text-xs font-bold text-slate-300 truncate w-24">{ent.name}</div>
                            </div>
                            <button className="opacity-0 group-hover:opacity-100 p-1 text-slate-600 hover:text-red-500 transition-all">
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))}
                    {placedEntities.length === 0 && <p className="text-[10px] italic text-slate-600 px-2">No entities placed yet.</p>}
                </div>

                <div className="p-6 bg-black/40 border-t border-white/5 space-y-3">
                    <button
                        onClick={async () => {
                            console.log("[ARCHITECT] Syncing Obsidian Vault...");
                            try {
                                const response = await fetch("http://localhost:8000/architect/sync/vault", {
                                    method: "POST"
                                });
                                const result = await response.json();
                                console.log("[ARCHITECT] Sync Result:", result);
                                alert("Vault Synced! Entities procedurally seeded.");
                                window.location.reload();
                            } catch (e) {
                                console.error("Sync Failed:", e);
                            }
                        }}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-cyan-600/10 hover:bg-cyan-600 text-cyan-500 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
                    >
                        <RefreshCw size={14} /> Sync Vault
                    </button>
                    <button
                        onClick={async () => {
                            console.log("[ARCHITECT] Starting Simulation...");
                            try {
                                const response = await fetch("http://localhost:8000/architect/simulate", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        entities: placedEntities,
                                        years: 50
                                    })
                                });
                                const result = await response.json();
                                console.log("[ARCHITECT] Sim Result:", result);
                                alert("Simulation Complete! History generated.");
                                window.location.reload(); // Refresh to see new ECS data
                            } catch (e) {
                                console.error("Sim Failed:", e);
                            }
                        }}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-yellow-600/10 hover:bg-yellow-600 text-yellow-500 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
                    >
                        <Play size={14} /> Run Simulation
                    </button>
                    <button className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all">
                        <Save size={14} /> Export World
                    </button>
                </div>
            </div>

            {/* CENTER: VIEWPORT */}
            <div className="flex-grow relative bg-[#0f0f13] flex items-center justify-center">
                <div className="absolute top-8 left-8 flex flex-col gap-4 z-10">
                    <div className="flex flex-col gap-2 bg-black/60 backdrop-blur-xl p-2 rounded-2xl border border-white/5">
                        <div className="flex items-center gap-3 px-2 py-1 text-[10px] font-bold tracking-widest text-slate-400">
                            <Layers size={14} className="text-yellow-500" />
                            MAP FOCUS: <span className="text-white uppercase font-black">{viewLayer} SECTOR</span>
                        </div>
                        <div className="flex items-center gap-1">
                            {(['GLOBAL', 'REGIONAL', 'LOCAL', 'TACTICAL'] as const).map(layer => (
                                <button
                                    key={layer}
                                    onClick={() => setViewLayer(layer)}
                                    className={clsx(
                                        "px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all",
                                        viewLayer === layer
                                            ? "bg-yellow-500/20 text-yellow-500 border border-yellow-500/20 shadow-[0_0_15px_rgba(234,179,8,0.15)]"
                                            : "text-slate-500 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    {layer}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* TIMELINE SCRUBBER */}
                    <div className="bg-black/60 backdrop-blur-3xl p-6 rounded-3xl border border-white/5 w-80 space-y-4 shadow-2xl animate-in fade-in slide-in-from-top-4 duration-700">
                        <div className="flex justify-between items-center">
                            <h3 className="text-[9px] font-black uppercase tracking-[0.2em] text-yellow-500 flex items-center gap-2">
                                <Play size={10} fill="currentColor" /> Timeline Shifter
                            </h3>
                            <span className="text-[10px] font-mono text-white/50">YEAR {currentYear}</span>
                        </div>

                        <input
                            type="range"
                            min={availableYears[0] || 0}
                            max={availableYears[availableYears.length - 1] || 100}
                            value={currentYear}
                            onChange={(e) => {
                                const year = parseInt(e.target.value);
                                handleTimelineScrub(year);
                            }}
                            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-yellow-500"
                        />

                        <div className="flex justify-between text-[8px] font-bold text-slate-600 tracking-tighter uppercase">
                            <span>Origin</span>
                            <span>Present Day</span>
                        </div>
                    </div>
                </div>

                <div className="w-full h-full flex items-center justify-center scale-95 hover:scale-100 transition-transform duration-700">
                    <MapCanvas
                        mapData={architectGrid || map}
                        entities={[...entities, ...placedEntities.map(e => ({ ...e, type: e.type.toLowerCase() as any }))] as any}
                        onCellClick={handleCanvasClick}
                        onCellDrag={handlePaint}
                    />
                </div>

                <div className="absolute top-8 right-8 flex gap-2 z-10">
                    <button
                        onClick={() => setAssetEditorOpen(true)}
                        className="p-4 bg-black/60 backdrop-blur-xl rounded-2xl border border-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all shadow-xl"
                        title="Open Asset Editor"
                    >
                        <Settings size={20} />
                    </button>
                </div>
            </div>

            <AssetEditor />

            {/* RIGHT: INSPECTOR */}
            {inspectorId && (
                <div className="w-80 border-l border-white/5 bg-[#0a0a0f]/80 backdrop-blur-3xl flex flex-col animate-in slide-in-from-right-2 duration-300 z-20">
                    <div className="p-8 border-b border-white/5 flex items-center justify-between">
                        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-yellow-500">Property Inspector</h3>
                        <button onClick={() => setInspectorId(null)} className="text-slate-600 hover:text-white">
                            <Trash2 size={16} />
                        </button>
                    </div>

                    <div className="p-8 space-y-8 overflow-y-auto">
                        <div className="space-y-4">
                            <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block">Entity Name</label>
                            <input
                                type="text"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-yellow-500/50 outline-none transition-all"
                                value={placedEntities.find(e => e.id === inspectorId)?.name}
                                onChange={(e) => updateEntity(inspectorId, { name: e.target.value })}
                            />
                        </div>

                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Aggression</label>
                                <span className="text-[10px] font-mono text-yellow-500">
                                    {Math.round((placedEntities.find(e => e.id === inspectorId)?.properties?.aggression || 0.5) * 100)}%
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0" max="1" step="0.01"
                                value={placedEntities.find(e => e.id === inspectorId)?.properties?.aggression || 0.5}
                                onChange={(e) => {
                                    const val = parseFloat(e.target.value);
                                    const ent = placedEntities.find(e => e.id === inspectorId);
                                    if (ent) {
                                        updateEntity(inspectorId, {
                                            properties: { ...ent.properties, aggression: val }
                                        });
                                    }
                                }}
                                className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-yellow-500"
                            />
                        </div>

                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Expansion Drive</label>
                                <span className="text-[10px] font-mono text-yellow-500">
                                    {Math.round((placedEntities.find(e => e.id === inspectorId)?.properties?.expansion || 0.5) * 100)}%
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0" max="1" step="0.01"
                                value={placedEntities.find(e => e.id === inspectorId)?.properties?.expansion || 0.5}
                                onChange={(e) => {
                                    const val = parseFloat(e.target.value);
                                    const ent = placedEntities.find(e => e.id === inspectorId);
                                    if (ent) {
                                        updateEntity(inspectorId, {
                                            properties: { ...ent.properties, expansion: val }
                                        });
                                    }
                                }}
                                className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-yellow-500"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Fertility</label>
                                    <span className="text-[10px] font-mono text-green-500">
                                        {Math.round((placedEntities.find(e => e.id === inspectorId)?.properties?.fertility || 0.1) * 100)}%
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min="0" max="1" step="0.01"
                                    value={placedEntities.find(e => e.id === inspectorId)?.properties?.fertility || 0.1}
                                    onChange={(e) => {
                                        const val = parseFloat(e.target.value);
                                        const ent = placedEntities.find(e => e.id === inspectorId);
                                        if (ent) {
                                            updateEntity(inspectorId, {
                                                properties: { ...ent.properties, fertility: val }
                                            });
                                        }
                                    }}
                                    className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-green-500"
                                />
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Tech Level</label>
                                    <span className="text-[10px] font-mono text-purple-500">
                                        {Math.round((placedEntities.find(e => e.id === inspectorId)?.properties?.techLevel || 0) * 10)}
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min="0" max="1" step="0.1"
                                    value={placedEntities.find(e => e.id === inspectorId)?.properties?.techLevel || 0}
                                    onChange={(e) => {
                                        const val = parseFloat(e.target.value);
                                        const ent = placedEntities.find(e => e.id === inspectorId);
                                        if (ent) {
                                            updateEntity(inspectorId, {
                                                properties: { ...ent.properties, techLevel: val }
                                            });
                                        }
                                    }}
                                    className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-purple-500"
                                />
                            </div>
                        </div>

                        {/* RESOURCE STOCKPILES */}
                        <div className="pt-4 border-t border-white/5 space-y-6">
                            <label className="text-[9px] font-black text-yellow-500 uppercase tracking-[0.2em] block">Starting Stockpiles</label>

                            {['food', 'wood', 'iron'].map(res => (
                                <div key={res} className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{res}</label>
                                        <span className="text-[10px] font-mono text-white/50">
                                            {placedEntities.find(e => e.id === inspectorId)?.properties?.resources?.[res] || 0}
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0" max="1000" step="10"
                                        value={placedEntities.find(e => e.id === inspectorId)?.properties?.resources?.[res] || 0}
                                        onChange={(e) => {
                                            const val = parseInt(e.target.value);
                                            const ent = placedEntities.find(e => e.id === inspectorId);
                                            if (ent) {
                                                const resources = ent.properties.resources || {};
                                                updateEntity(inspectorId, {
                                                    properties: { ...ent.properties, resources: { ...resources, [res]: val } }
                                                });
                                            }
                                        }}
                                        className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-slate-400"
                                    />
                                </div>
                            ))}
                        </div>

                        {/* RESOURCE NECESSITIES */}
                        <div className="pt-4 border-t border-white/5 space-y-6">
                            <label className="text-[9px] font-black text-yellow-500 uppercase tracking-[0.2em] block">Resource Dependency</label>

                            {['food', 'wood', 'iron'].map(res => (
                                <div key={`nec_${res}`} className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{res} Necessity</label>
                                        <span className="text-[10px] font-mono text-cyan-500">
                                            {Math.round((placedEntities.find(e => e.id === inspectorId)?.properties?.necessity?.[res] || 0.1) * 100)}%
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.01"
                                        value={placedEntities.find(e => e.id === inspectorId)?.properties?.necessity?.[res] || 0.1}
                                        onChange={(e) => {
                                            const val = parseFloat(e.target.value);
                                            const ent = placedEntities.find(e => e.id === inspectorId);
                                            if (ent) {
                                                const necessity = ent.properties.necessity || {};
                                                updateEntity(inspectorId, {
                                                    properties: { ...ent.properties, necessity: { ...necessity, [res]: val } }
                                                });
                                            }
                                        }}
                                        className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-cyan-500"
                                    />
                                </div>
                            ))}
                        </div>

                        {/* CULTURAL BEHAVIOR */}
                        <div className="pt-4 border-t border-white/5 space-y-6">
                            <label className="text-[9px] font-black text-yellow-500 uppercase tracking-[0.2em] block">Cultural Profiling</label>

                            <div className="space-y-4">
                                <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Cultural Hatred (Target)</label>
                                <select
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs focus:border-red-500/50 outline-none transition-all text-slate-300"
                                    value={placedEntities.find(e => e.id === inspectorId)?.properties?.hatred || "NONE"}
                                    onChange={(e) => {
                                        const ent = placedEntities.find(e => e.id === inspectorId);
                                        if (ent) {
                                            updateEntity(inspectorId, {
                                                properties: { ...ent.properties, hatred: e.target.value }
                                            });
                                        }
                                    }}
                                >
                                    <option value="NONE">No Targeted Hatred</option>
                                    <option value="ORC">Orcs (Xenophobist)</option>
                                    <option value="HUMAN">Humans (Xenophobist)</option>
                                    <option value="UNDEAD">Undead (Divine Hatred)</option>
                                </select>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Expansion Restraints</label>
                                <select
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs focus:border-yellow-500/50 outline-none transition-all text-slate-300"
                                    value={placedEntities.find(e => e.id === inspectorId)?.properties?.restraint || "NONE"}
                                    onChange={(e) => {
                                        const ent = placedEntities.find(e => e.id === inspectorId);
                                        if (ent) {
                                            updateEntity(inspectorId, {
                                                properties: { ...ent.properties, restraint: e.target.value }
                                            });
                                        }
                                    }}
                                >
                                    <option value="NONE">No Restraints</option>
                                    <option value="MOUNTAIN_ONLY">Mountain Only (Dwarven)</option>
                                    <option value="FOREST_ONLY">Forest Only (Elven)</option>
                                    <option value="COASTAL">Coastal Only (Seafarers)</option>
                                </select>
                            </div>
                        </div>

                        <div className="p-6 bg-yellow-500/5 border border-yellow-500/10 rounded-2xl">
                            <p className="text-[10px] text-yellow-500/80 leading-relaxed font-bold italic tracking-tight">
                                "High-Fidelity Profiling: Defining cultural desires, resource NECESSITIES, and expansion restraints provides the C++ engine with the sub-logic needed for varied historical evolution."
                            </p>
                        </div>
                    </div>

                    <div className="mt-auto p-8">
                        <button className="w-full py-4 bg-white/10 hover:bg-white/20 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest border border-white/10 transition-all flex items-center justify-center gap-2">
                            Update Registry <ChevronRight size={14} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
