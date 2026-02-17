import { X, Shield, Sword, Package, Zap, Heart, Brain } from 'lucide-react';
import { useGameStore } from '../store';
import { clsx } from 'clsx';
import { useState } from 'react';
import { ItemInspector } from './ItemInspector';

interface InventoryDrawerProps {
    isOpen: boolean;
    onClose: () => void;
}

export function InventoryDrawer({ isOpen, onClose }: InventoryDrawerProps) {
    const { entities, equipItem } = useGameStore();
    const [selectedItem, setSelectedItem] = useState<any>(null);
    const player = entities.find(e => e.type === 'player');

    if (!player) return null;

    return (
        <div className={clsx(
            "fixed inset-y-0 right-0 w-96 bg-[#050508]/95 backdrop-blur-3xl border-l border-white/5 shadow-[-50px_0_100px_rgba(0,0,0,0.5)] z-[100] transition-transform duration-500 ease-out",
            isOpen ? "translate-x-0" : "translate-x-full"
        )}>
            {/* Header */}
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                        <Shield size={16} className="text-yellow-500" />
                    </div>
                    <h2 className="text-xs font-black uppercase tracking-[0.2em] text-slate-200">Character & Gear</h2>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                    <X size={18} className="text-slate-500" />
                </button>
            </div>

            <div className="flex-grow overflow-y-auto p-6 space-y-8 custom-scrollbar h-[calc(100vh-80px)]">

                {/* Visual Stats Row */}
                <div className="grid grid-cols-3 gap-3">
                    <StatBox icon={<Heart size={14} />} label="Health" value={player.hp} max={player.maxHp} color="text-green-400" />
                    <StatBox icon={<Zap size={14} />} label="Stamina" value={player.sp || 0} max={player.maxSp || 0} color="text-yellow-400" />
                    <StatBox icon={<Brain size={14} />} label="Focus" value={player.fp || 0} max={player.maxFp || 0} color="text-blue-400" />
                </div>

                {/* Core Attributes */}
                <section className="space-y-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-white/5 pb-2">Core Attributes</h3>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                        {Object.entries(player.stats || {}).map(([name, val]) => (
                            <div key={name} className="flex justify-between items-center group">
                                <span className="text-[11px] text-slate-400 group-hover:text-slate-200 transition-colors">{name}</span>
                                <span className="text-sm font-black text-slate-100">{val}</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Equipment Loadout */}
                <section className="space-y-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-white/5 pb-2">Equipment Slots</h3>
                    <div className="grid grid-cols-1 gap-2">
                        {Object.entries(player.equipped || {}).map(([slot, item]) => (
                            <div key={slot} className="flex items-center gap-4 bg-[#12121a] p-3 rounded-xl border border-white/5 hover:border-yellow-500/30 transition-all group">
                                <div className="w-10 h-10 bg-black/40 rounded-lg flex items-center justify-center border border-white/5 text-slate-600 group-hover:text-yellow-500 transition-colors">
                                    {slot === 'MAIN_HAND' ? <Sword size={18} /> : <Shield size={18} />}
                                </div>
                                <div className="flex-grow">
                                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-tighter">{slot}</div>
                                    <div className="text-xs font-bold text-slate-200">{item || "EMPTY"}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Inventory */}
                <section className="space-y-4">
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-white/5 pb-2">Backpack</h3>
                    <div className="space-y-2">
                        {player.inventory?.map((item, idx) => {
                            const itemData = typeof item === 'string' ? { name: item, category: 'General', stats: { Info: 'Basic Item' } } : item;
                            return (
                                <div key={idx} className="flex items-center justify-between bg-[#12121a]/50 p-3 rounded-xl border border-white/5 hover:border-white/20 transition-all group">
                                    <div
                                        className="flex items-center gap-3 cursor-pointer flex-grow"
                                        onClick={() => setSelectedItem(itemData)}
                                    >
                                        <Package size={14} className="text-slate-500 group-hover:text-yellow-500 transition-colors" />
                                        <span className="text-xs text-slate-300 group-hover:text-white transition-colors">{itemData.name}</span>
                                    </div>
                                    <button
                                        onClick={() => equipItem(itemData.name, 'MAIN_HAND')}
                                        className="px-3 py-1 bg-white/5 hover:bg-yellow-600 hover:text-white rounded-lg text-[9px] font-black uppercase tracking-tighter transition-all"
                                    >
                                        Equip
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </section>
            </div>

            {selectedItem && (
                <ItemInspector
                    item={selectedItem}
                    onClose={() => setSelectedItem(null)}
                />
            )}
        </div>
    );
}

function StatBox({ icon, label, value, max, color }: any) {
    return (
        <div className="bg-[#12121a]/80 p-3 rounded-xl border border-white/5 flex flex-col items-center gap-1 shadow-2xl">
            <div className={color}>{icon}</div>
            <div className="text-[11px] font-black text-slate-100">{value}/{max}</div>
            <div className="text-[8px] font-bold text-slate-500 uppercase tracking-tighter">{label}</div>
        </div>
    );
}
