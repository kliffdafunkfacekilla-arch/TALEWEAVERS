import React from 'react';
import { useGameStore } from '../store';
import { X, Shield, Activity, Brain, Heart, Crosshair, Sword } from 'lucide-react';
import { clsx } from 'clsx';

export function CharacterSheet() {
    const { isCharacterSheetOpen, setCharacterSheetOpen, entities } = useGameStore();

    if (!isCharacterSheetOpen) return null;

    const player = entities.find(e => e.type === 'player');
    if (!player) return null;

    const stats = player.stats || {};
    const equipment = player.equipped || {};

    const StatRow = ({ label, value }: { label: string, value: number }) => (
        <div className="flex justify-between items-center py-2 border-b border-white/5">
            <span className="text-xs font-bold text-slate-400">{label}</span>
            <span className="text-sm font-black text-amber-500 font-mono">{value || 0}</span>
        </div>
    );

    const VitalBar = ({ label, current, max, colorClass, icon: Icon }: any) => {
        const pct = Math.min(100, Math.max(0, (current / max) * 100)) || 0;
        return (
            <div className="space-y-1">
                <div className="flex justify-between items-center text-[10px] font-black uppercase text-slate-500 tracking-widest">
                    <span className="flex items-center gap-1"><Icon size={12} className={colorClass} /> {label}</span>
                    <span className="text-white font-mono">{current} / {max}</span>
                </div>
                <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden border border-white/5">
                    <div className={clsx("h-full transition-all duration-500", colorClass.replace('text-', 'bg-'))} style={{ width: `${pct}%` }} />
                </div>
            </div>
        );
    }

    return (
        <>
            <div
                className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
                onClick={() => setCharacterSheetOpen(false)}
            />

            <div className="fixed top-0 left-16 bottom-0 w-[450px] bg-[#050508]/95 backdrop-blur-3xl border-r border-white/10 shadow-[20px_0_50px_rgba(0,0,0,0.5)] z-50 flex flex-col animate-in slide-in-from-left-4 duration-300">
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-gradient-to-r from-yellow-900/10 to-transparent">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-600 to-amber-800 p-0.5 shadow-lg shadow-yellow-900/20">
                            <div className="w-full h-full bg-[#0a0a0f] rounded-[10px] flex items-center justify-center">
                                <Shield size={24} className="text-yellow-500" />
                            </div>
                        </div>
                        <div>
                            <h2 className="text-lg font-black uppercase tracking-widest text-slate-200">{player.name || "Unknown Hero"}</h2>
                            <p className="text-[10px] font-bold text-yellow-500 uppercase tracking-[0.2em]">{player.Team || "Adventurer"}</p>
                        </div>
                    </div>
                    <button onClick={() => setCharacterSheetOpen(false)} className="p-2 bg-white/5 hover:bg-white/10 rounded-xl transition-all">
                        <X size={20} className="text-slate-400" />
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto p-6 space-y-8 custom-scrollbar">

                    {/* VITALS SECTION */}
                    <div className="space-y-4">
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-white/10 pb-2">Vitals</h3>
                        <div className="grid grid-cols-2 gap-6">
                            <VitalBar label="Health (HP)" current={player.hp} max={player.maxHp} colorClass="text-green-500" icon={Heart} />
                            <VitalBar label="Stamina (SP)" current={player.sp} max={player.maxSp} colorClass="text-orange-500" icon={Activity} />
                            <VitalBar label="Focus (FP)" current={player.fp} max={player.maxFp} colorClass="text-blue-500" icon={Brain} />
                            <VitalBar label="Composure (CMP)" current={player.cmp} max={player.maxCmp} colorClass="text-purple-500" icon={Crosshair} />
                        </div>
                    </div>

                    {/* ATTRIBUTES SECTION */}
                    <div className="space-y-4 shadow-xl shadow-black/50 bg-black/20 rounded-2xl p-4 border border-white/5">
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-white/10 pb-2 mb-4">Core Attributes</h3>
                        <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                            <StatRow label="Vitality" value={stats['Vitality']} />
                            <StatRow label="Endurance" value={stats['Endurance']} />
                            <StatRow label="Knowledge" value={stats['Knowledge']} />
                            <StatRow label="Willpower" value={stats['Willpower']} />
                            <StatRow label="Fortitude" value={stats['Fortitude']} />
                            <StatRow label="Might" value={stats['Might']} />
                            <StatRow label="Logic" value={stats['Logic']} />
                            <StatRow label="Intuition" value={stats['Intuition']} />
                            <StatRow label="Agility" value={stats['Agility']} />
                            <StatRow label="Reflexes" value={stats['Reflexes']} />
                            <StatRow label="Awareness" value={stats['Awareness']} />
                            <StatRow label="Deception" value={stats['Deception']} />
                        </div>
                    </div>

                    {/* EQUIPPED SECTION */}
                    <div className="space-y-4">
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-white/10 pb-2">Equipped Gear</h3>
                        <div className="space-y-2">
                            {['Head', 'Body', 'MainHand', 'OffHand', 'Accessory'].map(slot => (
                                <div key={slot} className="flex items-center gap-4 bg-white/5 border border-white/5 p-3 rounded-xl">
                                    <div className="w-10 h-10 rounded-lg bg-black/50 border border-white/10 flex flex-col items-center justify-center">
                                        {slot === 'MainHand' ? <Sword size={16} className="text-slate-600 mb-1" /> : <Shield size={16} className="text-slate-600 mb-1" />}
                                    </div>
                                    <div>
                                        <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{slot}</div>
                                        <div className="text-sm font-bold text-slate-200">
                                            {equipment[slot] ? equipment[slot].Name || equipment[slot] : 'Empty Slot'}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </>
    );
}
