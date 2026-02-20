import React from 'react';
import { useGameStore } from '../store';
import clsx from 'clsx';
import { Target, Scroll, CheckCircle2 } from 'lucide-react';

export const QuestTracker: React.FC = () => {
    const { quests } = useGameStore();

    if (!quests || quests.length === 0) return null;

    return (
        <div className="absolute top-4 right-4 w-72 bg-black/80 border border-amber-900/50 rounded pointer-events-auto backdrop-blur-md shadow-2xl overflow-hidden z-50">
            {/* Header */}
            <div className="bg-gradient-to-r from-amber-900/40 to-black/40 border-b border-amber-900/30 p-2 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-amber-500 font-serif">
                    <Scroll className="w-4 h-4" />
                    <span className="text-sm font-bold uppercase tracking-wider">Active Objectives</span>
                </div>
            </div>

            {/* Quests List */}
            <div className="p-3 space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                {quests.map((q: any) => {
                    const isComplete = q.status === "completed";
                    return (
                        <div key={q.id} className={clsx("flex flex-col space-y-1 transition-colors",
                            isComplete ? "opacity-50" : "opacity-100"
                        )}>
                            <div className="flex items-start space-x-2">
                                {isComplete ? (
                                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                                ) : (
                                    <Target className="w-4 h-4 text-red-500 mt-0.5 animate-pulse" />
                                )}
                                <span className={clsx("text-sm font-semibold",
                                    isComplete ? "text-gray-400 line-through" : "text-amber-100"
                                )}>
                                    {q.title}
                                </span>
                            </div>
                            <span className="text-xs text-gray-400 pl-6 italic break-words leading-tight">
                                {q.description}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
