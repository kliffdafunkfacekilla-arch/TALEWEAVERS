import React, { useEffect } from 'react';
import { X, Scroll, Sword, CheckCircle, Circle, Trophy } from 'lucide-react';
import { useGameStore } from '../store';
import { clsx } from 'clsx';

interface QuestLogProps {
    isOpen: boolean;
    onClose: () => void;
}

export const QuestLog: React.FC<QuestLogProps> = ({ isOpen, onClose }) => {
    const { quests, fetchQuests } = useGameStore();

    useEffect(() => {
        if (isOpen) fetchQuests();
    }, [isOpen]);

    return (
        <div className={clsx(
            "fixed inset-y-0 right-0 w-[450px] bg-[#050508]/95 backdrop-blur-3xl border-l border-white/5 shadow-[-50px_0_100px_rgba(0,0,0,0.5)] z-[100] transition-transform duration-500 ease-out",
            isOpen ? "translate-x-0" : "translate-x-full"
        )}>
            {/* Header */}
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/5">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-blue-500/10 rounded-lg border border-blue-500/20">
                        <Scroll size={16} className="text-blue-400" />
                    </div>
                    <h2 className="text-sm font-black uppercase tracking-[0.2em] text-slate-200">Chronicle of Deeds</h2>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                    <X size={18} className="text-slate-500" />
                </button>
            </div>

            <div className="p-6 h-[calc(100vh-80px)] overflow-y-auto custom-scrollbar space-y-6">
                {quests.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-center space-y-4 opacity-40">
                        <Scroll size={48} />
                        <p className="text-sm font-serif italic">Your chronicle is currently blank. Adventure awaits.</p>
                    </div>
                ) : (
                    quests.map((quest) => (
                        <div key={quest.id} className="bg-[#12121a] rounded-xl border border-white/5 overflow-hidden shadow-xl animate-in fade-in slide-in-from-right-4 duration-300">
                            {/* Quest Header */}
                            <div className="p-4 bg-white/5 border-b border-white/5">
                                <h3 className="text-lg font-serif text-white mb-1">{quest.title}</h3>
                                <p className="text-xs text-white/40 leading-relaxed">{quest.description}</p>
                            </div>

                            {/* Objectives */}
                            <div className="p-4 space-y-4">
                                <div className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Objectives</div>
                                <div className="space-y-3">
                                    {quest.objectives.map((obj: any, idx: number) => (
                                        <div key={idx} className="space-y-2">
                                            <div className="flex items-start gap-3">
                                                {obj.is_complete ? (
                                                    <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />
                                                ) : (
                                                    <Circle size={14} className="text-slate-600 mt-0.5 shrink-0" />
                                                )}
                                                <div className="flex-grow">
                                                    <div className={clsx(
                                                        "text-xs font-medium transition-colors",
                                                        obj.is_complete ? "text-slate-500 line-through" : "text-slate-200"
                                                    )}>
                                                        {obj.description}
                                                    </div>

                                                    {/* Progress Bar */}
                                                    {!obj.is_complete && obj.target_count > 1 && (
                                                        <div className="mt-2 w-full bg-black/40 h-1 rounded-full overflow-hidden border border-white/5">
                                                            <div
                                                                className="h-full bg-blue-500 transition-all duration-500"
                                                                style={{ width: `${(obj.current_count / obj.target_count) * 100}%` }}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Rewards */}
                            <div className="p-4 bg-black/40 border-t border-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-tighter">
                                    <div className="flex items-center gap-1.5 text-yellow-500">
                                        <Trophy size={12} /> {quest.rewards.gold} Gold
                                    </div>
                                    <div className="flex items-center gap-1.5 text-blue-400">
                                        <Zap size={12} /> {quest.rewards.xp} XP
                                    </div>
                                </div>
                                <div className="text-[9px] font-mono text-white/20 uppercase tracking-widest">
                                    Status: {quest.status}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
