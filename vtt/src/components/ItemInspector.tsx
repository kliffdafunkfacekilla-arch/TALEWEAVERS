import React from 'react';
import { X, Shield, Sword, Zap, Heart } from 'lucide-react';

interface ItemInspectorProps {
    item: any;
    onClose: () => void;
}

export const ItemInspector: React.FC<ItemInspectorProps> = ({ item, onClose }) => {
    if (!item) return null;

    const rarityColors: Record<string, string> = {
        "Tier 1": "border-gray-500 text-gray-400",
        "Tier 2": "border-blue-500 text-blue-400",
        "Tier 3": "border-purple-500 text-purple-400",
        "Tier 4": "border-amber-500 text-amber-400"
    };

    const colorClass = rarityColors[item.rarity] || "border-green-500 text-green-400";

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
            <div className={`w-full max-w-md bg-[#0a0a0c] border-2 ${colorClass.split(' ')[0]} rounded-xl shadow-2xl overflow-hidden animate-in zoom-in duration-200`}>
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-start bg-white/5">
                    <div>
                        <div className={`text-xs font-bold uppercase tracking-widest mb-1 ${colorClass.split(' ')[1]}`}>
                            {item.rarity || "Common Item"}
                        </div>
                        <h2 className="text-2xl font-serif text-white">{item.name}</h2>
                        <span className="text-xs text-white/40 italic">{item.category} • {item.material}</span>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors">
                        <X className="w-5 h-5 text-white/60" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-4">
                        {Object.entries(item.stats || {}).map(([key, val]: [string, any]) => (
                            <div key={key} className="bg-white/5 p-3 rounded-lg border border-white/5">
                                <div className="text-[10px] uppercase tracking-wider text-white/40 mb-1">{key}</div>
                                <div className="text-lg font-mono text-white">{val}</div>
                            </div>
                        ))}
                    </div>

                    {/* Effects/Traits */}
                    {(item.effects || item.traits) && (
                        <div className="space-y-3">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-white/60 flex items-center gap-2">
                                <Zap className="w-3 h-3" /> Magical Properties
                            </h3>
                            <div className="space-y-2">
                                {item.effects?.filter(Boolean).map((eff: string, i: number) => (
                                    <div key={i} className="text-sm text-blue-300 bg-blue-900/20 p-2 rounded-md border border-blue-800/30">
                                        {eff}
                                    </div>
                                ))}
                                {item.traits?.map((trait: string, i: number) => (
                                    <div key={i} className="text-sm text-amber-300 bg-amber-900/20 p-2 rounded-md border border-amber-800/30">
                                        {trait}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 bg-white/5 border-t border-white/10 flex justify-between items-center">
                    <div className="text-[10px] text-white/20 font-mono">ID: {item.id}</div>
                    <button
                        className="px-6 py-2 bg-white text-black font-bold rounded-lg hover:bg-white/90 transition-all active:scale-95"
                        onClick={onClose}
                    >
                        Equip
                    </button>
                </div>
            </div>
        </div>
    );
};
