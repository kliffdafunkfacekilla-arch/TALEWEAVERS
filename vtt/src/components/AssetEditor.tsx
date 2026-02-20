import React, { useState, useEffect } from 'react';
import { useArchitectStore } from '../architectStore';
import { X, Save, Plus, Database, Droplets, Thermometer, Box, Target, Briefcase } from 'lucide-react';
import { clsx } from 'clsx';

export function AssetEditor() {
    const { isAssetEditorOpen, setAssetEditorOpen, definedAssets, fetchAssets, saveAsset } = useArchitectStore();
    const [activeTab, setActiveTab] = useState<'species' | 'factions' | 'resources' | 'wildlife' | 'flora'>('species');
    const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
    const [editBuffer, setEditBuffer] = useState<any>(null);

    useEffect(() => {
        if (isAssetEditorOpen) {
            fetchAssets();
        }
    }, [isAssetEditorOpen]);

    if (!isAssetEditorOpen) return null;

    const list = definedAssets[activeTab] || [];

    const handleSelectAsset = (id: string) => {
        setSelectedAssetId(id);
        const original = list.find((a: any) => a.id === id);
        setEditBuffer(original ? JSON.parse(JSON.stringify(original)) : null);
    };

    const handleCreateNew = () => {
        const newId = `new_${Date.now()}`;
        let baseDef = { id: newId, name: `New ${activeTab}` };

        if (activeTab === 'species') {
            baseDef = { ...baseDef, growth_rate: 0.05, strength: 10, speed: 10, water_requirement: 0.5, min_temp_tolerance: -10, max_temp_tolerance: 40, task_weights: { farm: 1, mine: 1, hunt: 1, trade: 1, build: 1 }, resource_needs: {} } as any;
        } else if (activeTab === 'resources') {
            baseDef = { ...baseDef, category: 'material', rarity: 0.5, is_finite: false, spawn_biomes: [], bonuses: {} } as any;
        } else if (activeTab === 'factions') {
            baseDef = { ...baseDef, primary_species_id: '', aggression: 0.5, trade_focus: 0.5, expansion_drive: 0.5 } as any;
        }

        setSelectedAssetId(newId);
        setEditBuffer(baseDef);
    };

    const handleSave = async () => {
        if (!editBuffer) return;
        await saveAsset(activeTab, editBuffer);
        alert(`Saved ${editBuffer.name}!`);
    };

    const tabs = [
        { id: 'species', icon: Target, label: 'Species' },
        { id: 'factions', icon: Briefcase, label: 'Factions' },
        { id: 'resources', icon: Box, label: 'Resources' },
        { id: 'wildlife', icon: Database, label: 'Wildlife' },
        { id: 'flora', icon: Droplets, label: 'Flora' },
    ];

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-8 animate-in fade-in">
            <div className="w-[1000px] h-[800px] bg-[#0a0a0f] border border-white/10 rounded-3xl shadow-2xl flex overflow-hidden">

                {/* LEFT: TABS & LIST */}
                <div className="w-80 bg-black/40 border-r border-white/10 flex flex-col">
                    <div className="p-6 border-b border-white/10">
                        <h2 className="text-sm font-black uppercase tracking-widest text-yellow-500 flex items-center gap-2">
                            <Database size={16} /> Asset Definition Editor
                        </h2>
                    </div>

                    <div className="flex border-b border-white/10 overflow-x-auto overflow-y-hidden hide-scrollbar">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => { setActiveTab(tab.id as any); setSelectedAssetId(null); setEditBuffer(null); }}
                                className={clsx(
                                    "flex-shrink-0 flex items-center gap-2 px-6 py-4 text-[10px] font-bold uppercase tracking-widest transition-all",
                                    activeTab === tab.id
                                        ? "bg-yellow-500/10 text-yellow-500 border-b-2 border-yellow-500"
                                        : "text-slate-500 hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <tab.icon size={14} /> {tab.label}
                            </button>
                        ))}
                    </div>

                    <div className="flex-grow overflow-y-auto p-4 space-y-2">
                        {list.map((asset: any) => (
                            <button
                                key={asset.id}
                                onClick={() => handleSelectAsset(asset.id)}
                                className={clsx(
                                    "w-full text-left px-4 py-3 rounded-xl border text-xs font-bold transition-all",
                                    selectedAssetId === asset.id
                                        ? "bg-white/10 border-white/20 text-white"
                                        : "bg-transparent border-transparent text-slate-400 hover:bg-white/5 hover:border-white/10"
                                )}
                            >
                                {asset.name}
                            </button>
                        ))}
                    </div>

                    <div className="p-4 border-t border-white/10">
                        <button
                            onClick={handleCreateNew}
                            className="w-full flex items-center justify-center gap-2 py-3 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
                        >
                            <Plus size={14} /> Create New {activeTab}
                        </button>
                    </div>
                </div>

                {/* RIGHT: EDITOR SURFACE */}
                <div className="flex-grow flex flex-col">
                    <div className="p-6 border-b border-white/10 flex justify-between items-center">
                        <div>
                            <h3 className="text-lg font-bold text-white mb-1">
                                {editBuffer ? editBuffer.name : "Select an asset"}
                            </h3>
                            <p className="text-[10px] uppercase tracking-widest text-slate-500">
                                {editBuffer && `ID: ${editBuffer.id}`}
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            {editBuffer && (
                                <button
                                    onClick={handleSave}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-yellow-500 text-black hover:bg-yellow-400 rounded-xl text-xs font-black uppercase tracking-widest transition-all"
                                >
                                    <Save size={14} /> Save Changes
                                </button>
                            )}
                            <button onClick={() => setAssetEditorOpen(false)} className="p-3 bg-white/5 hover:bg-white/10 text-white rounded-full transition-all">
                                <X size={20} />
                            </button>
                        </div>
                    </div>

                    <div className="flex-grow p-8 overflow-y-auto">
                        {!editBuffer && (
                            <div className="h-full flex items-center justify-center text-slate-500 text-sm font-mono">
                                No asset selected.
                            </div>
                        )}

                        {editBuffer && (
                            <div className="max-w-xl space-y-8">
                                {/* STANDARD FIELDS */}
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">ID (Snake_Case)</label>
                                    <input
                                        type="text"
                                        value={editBuffer.id}
                                        onChange={(e) => setEditBuffer({ ...editBuffer, id: e.target.value })}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-mono focus:border-yellow-500/50 outline-none"
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Display Name</label>
                                    <input
                                        type="text"
                                        value={editBuffer.name}
                                        onChange={(e) => setEditBuffer({ ...editBuffer, name: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:border-yellow-500/50 outline-none"
                                    />
                                </div>

                                {/* DYNAMIC FIELDS BASED ON CATEGORY */}
                                {activeTab === 'species' && (
                                    <>
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-4">
                                                <label className="text-[10px] font-black flex items-center gap-2 text-cyan-500 uppercase tracking-widest">
                                                    <Droplets size={12} /> Water Eq.
                                                </label>
                                                <input
                                                    type="range" min="0" max="1" step="0.05"
                                                    value={editBuffer.water_requirement}
                                                    onChange={(e) => setEditBuffer({ ...editBuffer, water_requirement: parseFloat(e.target.value) })}
                                                    className="w-full h-1.5 rounded-full appearance-none bg-white/10 accent-cyan-500"
                                                />
                                                <div className="text-right text-xs text-slate-500 font-mono">{Math.round(editBuffer.water_requirement * 100)}%</div>
                                            </div>

                                            <div className="space-y-4">
                                                <label className="text-[10px] font-black flex items-center gap-2 text-orange-500 uppercase tracking-widest">
                                                    <Thermometer size={12} /> Temp Range (°C)
                                                </label>
                                                <div className="flex items-center gap-4">
                                                    <input
                                                        type="number"
                                                        value={editBuffer.min_temp_tolerance}
                                                        onChange={(e) => setEditBuffer({ ...editBuffer, min_temp_tolerance: parseFloat(e.target.value) })}
                                                        className="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none"
                                                    />
                                                    <span className="text-slate-500">to</span>
                                                    <input
                                                        type="number"
                                                        value={editBuffer.max_temp_tolerance}
                                                        onChange={(e) => setEditBuffer({ ...editBuffer, max_temp_tolerance: parseFloat(e.target.value) })}
                                                        className="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="p-6 bg-white/5 rounded-2xl border border-white/10 space-y-6">
                                            <h4 className="text-[10px] font-black text-yellow-500 uppercase tracking-widest">Task Willingness Weights</h4>

                                            {['farm', 'mine', 'hunt', 'trade', 'build'].map(task => (
                                                <div key={task} className="space-y-2">
                                                    <div className="flex justify-between items-center text-xs">
                                                        <span className="text-slate-400 capitalize">{task}</span>
                                                        <span className="text-slate-500 font-mono">{editBuffer.task_weights?.[task] || 1.0}x</span>
                                                    </div>
                                                    <input
                                                        type="range" min="0" max="3" step="0.1"
                                                        value={editBuffer.task_weights?.[task] || 1.0}
                                                        onChange={(e) => setEditBuffer({
                                                            ...editBuffer,
                                                            task_weights: { ...editBuffer.task_weights, [task]: parseFloat(e.target.value) }
                                                        })}
                                                        className="w-full h-1 bg-white/10 rounded-full appearance-none accent-yellow-500"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                )}

                                {activeTab === 'resources' && (
                                    <>
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-4">
                                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Category</label>
                                                <select
                                                    value={editBuffer.category}
                                                    onChange={(e) => setEditBuffer({ ...editBuffer, category: e.target.value })}
                                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none"
                                                >
                                                    <option value="food">Food</option>
                                                    <option value="material">Material</option>
                                                    <option value="wealth">Wealth</option>
                                                    <option value="luxury">Luxury Item</option>
                                                </select>
                                            </div>
                                            <div className="space-y-4">
                                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Rarity</label>
                                                <input
                                                    type="range" min="0" max="1" step="0.05"
                                                    value={editBuffer.rarity}
                                                    onChange={(e) => setEditBuffer({ ...editBuffer, rarity: parseFloat(e.target.value) })}
                                                    className="w-full h-1.5 rounded-full appearance-none bg-white/10 accent-purple-500"
                                                />
                                                <div className="text-right text-xs text-slate-500 font-mono">{(editBuffer.rarity * 100).toFixed(0)}%</div>
                                            </div>
                                            <div className="space-y-4">
                                                <label className="flex items-center gap-3 text-sm text-slate-300 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={editBuffer.is_finite}
                                                        onChange={(e) => setEditBuffer({ ...editBuffer, is_finite: e.target.checked })}
                                                        className="w-5 h-5 accent-red-500 bg-white/10 border-white/10 rounded"
                                                    />
                                                    Is Finite (Cannot Respawn)
                                                </label>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
