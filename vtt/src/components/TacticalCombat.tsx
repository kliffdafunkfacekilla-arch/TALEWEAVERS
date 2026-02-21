import { useEffect, useState } from 'react';
import { useGameStore } from '../store';
import { MapCanvas } from './MapCanvas';
import { Skull, Move, Sword, RefreshCw, User, ChevronRight, MessageSquare } from 'lucide-react';
import { clsx } from 'clsx';

export function TacticalCombat() {
    const { log, addLog } = useGameStore();
    const [saves, setSaves] = useState<string[]>([]);
    const [selectedSave, setSelectedSave] = useState<string | null>(null);
    const [combatState, setCombatState] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [hoverInfo, setHoverInfo] = useState<{ x: number, y: number, type: string } | null>(null);
    const [isSmashMode, setIsSmashMode] = useState(false);
    const [vEvents, setVEvents] = useState<any[]>([]);

    useEffect(() => {
        fetchSaves();
    }, []);

    const fetchSaves = async () => {
        const res = await fetch('/api/combat/saves');
        if (res.ok) setSaves(await res.json());
    };

    const loadCharacter = async (name: string) => {
        setIsLoading(true);
        setSelectedSave(name);
        try {
            const res = await fetch('/api/combat/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ character_name: name })
            });
            if (res.ok) {
                const data = await res.json();
                setCombatState(data);
                addLog(`Loaded ${name} into the Battle Lab.`);
                syncState();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    const syncState = async () => {
        const res = await fetch('/api/combat/state');
        if (res.ok) {
            const data = await res.json();
            setCombatState(prev => ({ ...prev, ...data }));
        }
    };

    const handleAction = async (action: string, params: any = {}) => {
        const res = await fetch('/api/combat/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, ...params })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.narrative) addLog(data.narrative, 'system');
            if (data.updates) setVEvents(data.updates);
            syncState();
        }
    };

    const handleEndTurn = async () => {
        setIsLoading(true);
        try {
            const res = await fetch('/api/combat/end_turn', { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                addLog("End of Round. AI processing actions...", 'system');
                if (data.updates) setVEvents(data.updates);
                await syncState();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    const player = combatState?.entities?.find((e: any) => e.tags?.includes('hero'));

    return (
        <div className="flex h-full w-full bg-[#0a0a0f]">
            {/* SIDEBAR: CHARACTER SELECT */}
            <div className="w-80 border-r border-white/5 bg-[#050508]/60 backdrop-blur-3xl flex flex-col p-6 overflow-hidden">
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                        <Skull size={20} className="text-yellow-500" />
                    </div>
                    <div>
                        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-yellow-500">Battle Lab</h2>
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">v1.0 Proving Grounds</p>
                    </div>
                </div>

                <div className="flex-grow overflow-y-auto space-y-2 custom-scrollbar pr-2">
                    <h3 className="text-[10px] font-black text-slate-500 uppercase mb-4 tracking-tighter">Select Unit to Deploy</h3>
                    {saves.map(save => (
                        <div
                            key={save}
                            onClick={() => loadCharacter(save)}
                            className={clsx(
                                "p-4 rounded-xl border flex items-center justify-between transition-all cursor-pointer group",
                                selectedSave === save
                                    ? "bg-yellow-500/10 border-yellow-500/40 shadow-[0_0_20px_rgba(234,179,8,0.1)]"
                                    : "bg-white/5 border-white/5 hover:border-white/10"
                            )}
                        >
                            <div className="flex items-center gap-3">
                                <User size={16} className={selectedSave === save ? "text-yellow-500" : "text-slate-500"} />
                                <span className={clsx("text-sm font-bold", selectedSave === save ? "text-white" : "text-slate-400")}>{save}</span>
                            </div>
                            <ChevronRight size={14} className="text-slate-600 group-hover:text-yellow-500 transition-colors" />
                        </div>
                    ))}
                </div>
            </div>

            {/* MAIN GRID */}
            <div className="flex-grow relative flex flex-col overflow-hidden">
                <div className="flex-grow">
                    {combatState ? (
                        <MapCanvas
                            mapData={{
                                width: 10,
                                height: 10,
                                grid: combatState.grid?.cells || Array(10).fill(Array(10).fill(128)),
                                biome: 'arena'
                            }}
                            entities={combatState.entities || []}
                            visualEvents={vEvents}
                            onCellClick={(x, y) => {
                                if (!player) return;

                                if (isSmashMode) {
                                    handleAction('SMASH', { x, y });
                                    setIsSmashMode(false);
                                    return;
                                }

                                const clickedEntity = combatState.entities.find((e: any) => e.pos[0] === x && e.pos[1] === y);

                                if (clickedEntity && clickedEntity.id !== player.id) {
                                    handleAction('ATTACK', { target_id: clickedEntity.id });
                                } else {
                                    const dx = x - player.pos[0];
                                    const dy = y - player.pos[1];
                                    if (Math.abs(dx) <= 1 && Math.abs(dy) <= 1 && (dx !== 0 || dy !== 0)) {
                                        handleAction('MOVE', { dx, dy });
                                    }
                                }
                            }}
                            onCellHover={(x, y) => {
                                if (y === null) {
                                    setHoverInfo(null);
                                    return;
                                }
                                const cell = combatState.grid?.cells?.[y]?.[x];
                                let type = "Clear";
                                if (cell === 896) type = "Wall (Obstructing)";
                                if (cell === 130) type = "Bushes (Difficult)";
                                setHoverInfo({ x, y, type });
                            }}
                            range={player ? Math.floor(player.sp) : 0}
                            origin={player ? player.pos : [0, 0]}
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center flex-col gap-4 text-slate-500">
                            <Skull size={48} className="opacity-10 animate-pulse" />
                            <span className="text-xs uppercase tracking-[0.4em] font-black">Waiting for Deployment...</span>
                        </div>
                    )}
                </div>

                {/* BOTTOM OVERLAY: CONTROLS & STATS */}
                {player && (
                    <div className="h-32 border-t border-white/5 bg-[#050508]/80 backdrop-blur-2xl flex items-center px-12 gap-12 z-20">
                        <div className="flex items-center gap-4">
                            <img src="/api/placeholder/40/40" alt="Icon" className="w-12 h-12 rounded-xl border border-white/10 bg-black" />
                            <div>
                                <h4 className="text-sm font-black text-white uppercase">{player.name}</h4>
                                <div className="flex gap-2 text-[10px] text-yellow-500/80 font-bold uppercase tracking-widest">
                                    <span>Lvl 1</span>
                                    <span>•</span>
                                    <span>Vanguard</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-8 border-l border-white/10 pl-12">
                            <div>
                                <div className="text-[9px] font-black text-slate-500 uppercase mb-1">Vitality</div>
                                <div className="text-lg font-black text-red-400 leading-none">{player.hp}<span className="text-slate-600 text-xs ml-1">/{player.maxHp}</span></div>
                            </div>
                            <div>
                                <div className="text-[9px] font-black text-slate-500 uppercase mb-1">Stamina</div>
                                <div className="text-lg font-black text-green-400 leading-none">{player.sp}<span className="text-slate-600 text-xs ml-1">/{player.maxSp}</span></div>
                            </div>
                            <div>
                                <div className="text-[9px] font-black text-slate-500 uppercase mb-1">Focus</div>
                                <div className="text-lg font-black text-blue-400 leading-none">{player.fp}<span className="text-slate-600 text-xs ml-1">/{player.maxFp}</span></div>
                            </div>
                        </div>

                        <div className="flex-grow flex justify-center gap-4">
                            <button
                                onClick={() => handleAction('ATTACK', { target_id: 'Target Dummy' })}
                                className="flex items-center gap-3 px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(220,38,38,0.2)]"
                            >
                                <Sword size={16} /> Assault Strike
                            </button>
                            <button className="flex items-center gap-3 px-6 py-3 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/5">
                                <Move size={16} /> Dash (3 SP)
                            </button>
                            <button
                                onClick={() => setIsSmashMode(!isSmashMode)}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    isSmashMode
                                        ? "bg-orange-600 border-orange-400 text-white shadow-[0_0_20px_rgba(234,88,12,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <Skull size={16} /> Might: Smash (3 SP)
                            </button>
                            <button
                                onClick={handleEndTurn}

                                disabled={isLoading}
                                className="flex items-center gap-3 px-6 py-3 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(217,119,6,0.2)] disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} /> End Turn
                            </button>
                        </div>

                        <button onClick={syncState} className="p-3 text-slate-500 hover:text-white hover:bg-white/5 rounded-xl transition-all">
                            <RefreshCw size={20} />
                        </button>
                    </div>
                )}
            </div>

            {/* RIGHT SIDEBAR: LOG */}
            <div className="w-80 border-l border-white/5 bg-[#050508]/60 backdrop-blur-3xl flex flex-col">
                <div className="p-6 border-b border-white/5 flex items-center gap-2">
                    <MessageSquare size={16} className="text-slate-400" />
                    <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-300">Tactical Feed</h2>
                </div>

                {hoverInfo && (
                    <div className="px-6 py-4 bg-yellow-500/5 border-b border-white/5">
                        <div className="text-[9px] font-black text-yellow-500 uppercase tracking-widest mb-1">Targeting {hoverInfo.x}, {hoverInfo.y}</div>
                        <div className="text-xs font-bold text-white uppercase">{hoverInfo.type}</div>
                    </div>
                )}

                <div className="flex-grow p-6 overflow-y-auto space-y-3 font-mono text-[10px] custom-scrollbar">
                    {combatState?.log?.map((entry: string, i: number) => (
                        <div key={i} className="text-slate-400 border-l border-white/10 pl-3 py-1 mb-1">
                            {entry}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
