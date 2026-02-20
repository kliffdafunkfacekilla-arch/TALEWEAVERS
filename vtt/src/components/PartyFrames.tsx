import React from 'react';
import { useGameStore } from '../store';
import { Shield, Brain } from 'lucide-react';
import { clsx } from 'clsx';

export function PartyFrames() {
    const { entities, activePlayerId, setActivePlayerId } = useGameStore();

    // Find all controllable entities (type player or ally)
    const partyMembers = entities.filter(e => e.type === 'player' || e.type === 'ally');

    if (partyMembers.length === 0) return null;

    return (
        <div className="absolute left-8 top-32 flex flex-col gap-4 z-30 pointer-events-none">
            {partyMembers.map(member => {
                const isActive = activePlayerId === member.id;
                const hpPct = Math.min(100, Math.max(0, (member.hp / (member.maxHp || member.hp || 1)) * 100)) || 0;

                return (
                    <div
                        key={member.id}
                        onClick={() => setActivePlayerId(member.id)}
                        className={clsx(
                            "pointer-events-auto flex items-center gap-4 bg-[#0a0a0f]/90 border backdrop-blur-md rounded-2xl p-3 shadow-2xl transition-all cursor-pointer",
                            isActive
                                ? "border-yellow-500/50 shadow-[0_0_20px_rgba(234,179,8,0.2)] scale-105"
                                : "border-white/10 hover:border-white/20 hover:bg-white/5 opacity-80"
                        )}
                    >
                        {/* Avatar */}
                        <div className={clsx(
                            "w-12 h-12 rounded-xl flex items-center justify-center border",
                            isActive ? "bg-gradient-to-br from-yellow-600 to-amber-800 border-yellow-500/50" : "bg-black/50 border-white/10"
                        )}>
                            <Shield size={20} className={isActive ? "text-white" : "text-slate-500"} />
                        </div>

                        {/* Stats */}
                        <div className="w-32">
                            <h3 className={clsx("text-xs font-black uppercase tracking-widest truncate", isActive ? "text-yellow-500" : "text-slate-300")}>
                                {member.name}
                            </h3>

                            <div className="mt-2 space-y-1.5">
                                {/* HP BAR */}
                                <div>
                                    <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden border border-white/5">
                                        <div className="h-full bg-green-500 transition-all duration-300" style={{ width: `${hpPct}%` }} />
                                    </div>
                                </div>

                                {/* SP BAR (Proxy/Dummy if missing) */}
                                <div>
                                    <div className="w-full h-1 bg-black/60 rounded-full overflow-hidden border border-white/5">
                                        <div className="h-full bg-orange-500 transition-all duration-300" style={{ width: '100%' }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
