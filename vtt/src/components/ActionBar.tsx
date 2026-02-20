import React from 'react';
import { useGameStore } from '../store';
import { Sword, Shield, Footprints, Flame, Sparkles, Wind, Eye, Hand } from 'lucide-react';
import { clsx } from 'clsx';

export function ActionBar() {
    const { castSkill, useItem, camp, selectedEntityId, addLog, isDMThinking, entities } = useGameStore();

    const player = entities.find(e => e.type === 'player');

    if (!player) return null;

    const actions = [
        { id: 'STRIKER', icon: Sword, label: 'Melee Strike', type: 'skill', requiresTarget: true, color: 'text-red-500' },
        { id: 'SNIPER', icon: Target, label: 'Ranged Shot', type: 'skill', requiresTarget: true, color: 'text-orange-500' },
        { id: 'FIREBALL', icon: Flame, label: 'Fireball', type: 'skill', requiresTarget: true, color: 'text-orange-600' },
        { id: 'potion_hp_minor', icon: Sparkles, label: 'Minor Potion', type: 'item', color: 'text-green-400' },
        { id: 'search', icon: Eye, label: 'Search', type: 'skill', color: 'text-yellow-400' },
        { id: 'camp', icon: Hand, label: 'Set Camp', type: 'camp', color: 'text-purple-400' }
    ];

    const handleActionClick = (action: any) => {
        if (isDMThinking) return;

        if (action.type === 'skill') {
            if (action.requiresTarget && !selectedEntityId) {
                addLog(`You must select a target to use ${action.label}!`, 'system');
                return;
            }
            castSkill(action.id, selectedEntityId || undefined);
        } else if (action.type === 'item') {
            useItem(action.id);
        } else if (action.type === 'camp') {
            camp();
        }
    };

    return (
        <div className="absolute bottom-32 left-1/2 -translate-x-1/2 w-full max-w-3xl px-6 flex justify-center z-40 pointer-events-none">
            <div className="flex items-center gap-2 p-3 bg-[#0a0a0f]/90 border border-white/10 backdrop-blur-2xl rounded-2xl shadow-2xl pointer-events-auto">
                {actions.map((action, i) => {
                    const Icon = action.icon;
                    return (
                        <div key={action.id} className="relative group flex flex-col items-center">
                            <button
                                onClick={() => handleActionClick(action)}
                                disabled={isDMThinking}
                                className={clsx(
                                    "w-12 h-12 rounded-xl flex items-center justify-center transition-all bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100",
                                    action.color
                                )}
                            >
                                <Icon size={22} className="drop-shadow-lg" />
                            </button>
                            <span className="absolute -top-8 bg-black border border-white/10 text-[10px] font-black uppercase text-white px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                                {action.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// Temporary icon mock for Target since it's not imported above
function Target(props: any) {
    return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" /></svg>
}
