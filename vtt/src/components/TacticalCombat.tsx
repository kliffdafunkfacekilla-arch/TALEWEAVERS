import { useEffect, useState } from 'react';
import { useGameStore } from '../store';
import { MapCanvas } from './MapCanvas';
import { Skull, Move, Sword, RefreshCw, User, ChevronRight, MessageSquare, Droplets, Zap, Link, Wind, Flame, MoveUp, Database } from 'lucide-react';
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
    const [targetingSkill, setTargetingSkill] = useState<string | null>(null);

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

    const handleExportCombat = async () => {
        setIsLoading(true);
        try {
            const res = await fetch('/api/combat/export_combat', { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                addLog(`Combat exported successfully: ${data.file}`, 'system');
                setCombatState(null); // Reset view
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
                                biome: 'arena',
                                hoveredEntity: hoverInfo?.entity,
                                threat: combatState.grid?.threat,
                                terrain: combatState.grid?.terrain,
                                items: combatState.grid?.items,
                                elevation: combatState.grid?.elevation
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

                                if (targetingSkill) {
                                    handleAction('SKILL', { skill_name: targetingSkill, x, y });
                                    setTargetingSkill(null);
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
                                const entity = combatState.entities?.find((e: any) => e.pos[0] === x && e.pos[1] === y);

                                let type = "Clear Ground";
                                if (cell === 896) type = "Wall (Obstructing)";
                                if (cell === 130) type = "Bushes (Difficult)";

                                setHoverInfo({
                                    x, y,
                                    type,
                                    entity: entity ? {
                                        name: entity.name,
                                        hp: entity.hp,
                                        maxHp: entity.maxHp,
                                        pos: entity.pos,
                                        traits: entity.metadata?.Traits || {},
                                        status: entity.statusEffects || []
                                    } : null
                                });
                            }}
                            visualEvents={vEvents}
                            range={targetingSkill === 'SHOCKING BURST' ? 2 : (targetingSkill === 'ACID SPIT' ? 5 : (targetingSkill === 'GRAPPLING LASH' ? 4 : (targetingSkill === 'JUMP' ? 3 : (player ? Math.floor(player.sp) : 0))))}
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

                            <div className="h-full w-px bg-white/10 mx-2" />

                            <button
                                onClick={() => { setTargetingSkill(targetingSkill === 'ACID SPIT' ? null : 'ACID SPIT'); setIsSmashMode(false); }}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    targetingSkill === 'ACID SPIT'
                                        ? "bg-lime-600 border-lime-400 text-white shadow-[0_0_20px_rgba(132,204,22,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <Droplets size={16} /> Acid Spit (4 SP)
                            </button>

                            <button
                                onClick={() => { setTargetingSkill(targetingSkill === 'SHOCKING BURST' ? null : 'SHOCKING BURST'); setIsSmashMode(false); }}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    targetingSkill === 'SHOCKING BURST'
                                        ? "bg-blue-600 border-blue-400 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <Zap size={16} /> Shock Burst (6 SP)
                            </button>

                            <button
                                onClick={() => { setTargetingSkill(targetingSkill === 'GRAPPLING LASH' ? null : 'GRAPPLING LASH'); setIsSmashMode(false); }}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    targetingSkill === 'GRAPPLING LASH'
                                        ? "bg-indigo-600 border-indigo-400 text-white shadow-[0_0_20px_rgba(79,70,229,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <Link size={16} /> Lash (5 SP)
                            </button>

                            <button
                                onClick={() => handleAction('SKILL', { skill_name: 'TAUNTING ROAR' })}
                                className="flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/5 text-red-300 hover:bg-red-900/20 hover:border-red-900/30 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all"
                            >
                                <Wind size={16} /> Taunting Roar (4 SP)
                            </button>

                            <button
                                onClick={() => { setTargetingSkill(targetingSkill === 'KINETIC SHOVE' ? null : 'KINETIC SHOVE'); setIsSmashMode(false); }}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    targetingSkill === 'KINETIC SHOVE'
                                        ? "bg-orange-600 border-orange-400 text-white shadow-[0_0_20px_rgba(234,88,12,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <Move size={16} /> Kinetic Shove (4 SP)
                            </button>

                            <button
                                onClick={() => { setTargetingSkill(targetingSkill === 'JUMP' ? null : 'JUMP'); setIsSmashMode(false); }}
                                className={clsx(
                                    "flex items-center gap-3 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border",
                                    targetingSkill === 'JUMP'
                                        ? "bg-purple-600 border-purple-400 text-white shadow-[0_0_20px_rgba(147,51,234,0.4)]"
                                        : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10"
                                )}
                            >
                                <MoveUp size={16} /> Jump (3 SP)
                            </button>

                            <button
                                onClick={() => handleAction('SKILL', { skill_name: 'PRIMAL FURY' })}
                                className="flex items-center gap-3 px-6 py-3 bg-red-900/40 border border-red-500/50 text-red-200 hover:bg-red-800/60 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(239,68,68,0.2)]"
                            >
                                <Flame size={16} /> Primal Fury (5 SP)
                            </button>

                            <div className="h-full w-px bg-white/10 mx-2" />

                            <button className="flex items-center gap-3 px-6 py-3 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/5">
                                <Move size={16} /> Dash (3 SP)
                            </button>
                            <button
                                onClick={() => { setIsSmashMode(!isSmashMode); setTargetingSkill(null); }}
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
                            <button
                                onClick={handleExportCombat}
                                disabled={isLoading}
                                className="flex items-center gap-3 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(8,145,178,0.2)] disabled:opacity-50"
                            >
                                <Database size={16} /> Sync & End Combat
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
                    <div className="px-6 py-4 bg-white/5 border-b border-white/5">
                        <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Targeting {hoverInfo.x}, {hoverInfo.y}</div>
                        <div className="text-xs font-bold text-white uppercase mb-2">{hoverInfo.type}</div>

                        {hoverInfo.entity && (
                            <div className="mt-4 p-3 bg-black/40 rounded-lg border border-white/5">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-[10px] font-black text-yellow-500 uppercase">{hoverInfo.entity.name}</span>
                                    <span className="text-[10px] font-bold text-red-400">{hoverInfo.entity.hp}/{hoverInfo.entity.maxHp} HP</span>
                                </div>

                                {Object.keys(hoverInfo.entity.traits).length > 0 && (
                                    <div className="mb-2">
                                        <div className="text-[8px] font-black text-slate-600 uppercase mb-1">Traits</div>
                                        <div className="flex flex-wrap gap-1">
                                            {Object.keys(hoverInfo.entity.traits).map(t => (
                                                <span key={t} className="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 text-[8px] font-bold rounded border border-blue-500/20">{t}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {hoverInfo.entity.status.length > 0 && (
                                    <div>
                                        <div className="text-[8px] font-black text-slate-600 uppercase mb-1">Status</div>
                                        <div className="flex flex-wrap gap-1">
                                            {hoverInfo.entity.status.map((s: any) => (
                                                <span key={s.type} className="px-1.5 py-0.5 bg-red-500/10 text-red-400 text-[8px] font-bold rounded border border-red-500/20">{s.type}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                <div className="flex-grow p-6 overflow-y-auto space-y-3 font-mono text-[10px] custom-scrollbar flex flex-col-reverse">
                    {[...(combatState?.log || [])].reverse().map((entry: string, i: number) => {
                        let colorClass = "text-slate-400";
                        if (entry.includes("[ADAPT]")) colorClass = "text-cyan-400 font-bold";
                        if (entry.includes("[SYMBIO]")) colorClass = "text-pink-400 font-bold";
                        if (entry.includes("[RESISTED]")) colorClass = "text-blue-300 italic";
                        if (entry.includes("PRIMAL FURY") || entry.includes("ENRAGED")) colorClass = "text-red-500 font-black";
                        if (entry.includes("ACID")) colorClass = "text-lime-400";
                        if (entry.includes("LAVA") || entry.includes("scorch")) colorClass = "text-orange-500";

                        return (
                            <div key={i} className={clsx("border-l border-white/10 pl-3 py-1", colorClass)}>
                                {entry}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
