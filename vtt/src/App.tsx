import { useEffect, useState } from 'react';
import { MapCanvas } from './components/MapCanvas';
import { InventoryDrawer } from './components/InventoryDrawer';
import { QuestLog } from './components/QuestLog';
import { QuestTracker } from './components/QuestTracker';
import { ActionBar } from './components/ActionBar';
import { CharacterSheet } from './components/CharacterSheet';
import { CharacterCreator } from './components/CharacterCreator';
import { PartyFrames } from './components/PartyFrames';
import { useGameStore } from './store';
import { Terminal, Scroll, Skull, Shield, Sword, MessageSquare, Sparkles, LayoutGrid, Hammer, User } from 'lucide-react';
import { clsx } from 'clsx';
import { WorldArchitect } from './components/WorldArchitect';
import { TacticalCombat } from './components/TacticalCombat';

function App() {
    const [viewMode, setViewMode] = useState<'PLAY' | 'ARCHITECT' | 'BATTLE_LAB'>('PLAY');
    const {
        meta, map, log, fetchNewSession, submitResult, entities, dmChat, isDMThinking,
        isInventoryOpen, setInventoryOpen, isQuestLogOpen, setQuestLogOpen,
        isCharacterSheetOpen, setCharacterSheetOpen,
        isCharacterCreatorOpen, setCharacterCreatorOpen,
        round, turn_order, active_combatant,
        playerMapView, setPlayerMapView, architectGrid, fetchArchitectGrid,
        activePlayerId
    } = useGameStore();

    const [dmInput, setDmInput] = useState("");

    useEffect(() => {
        fetchNewSession();
        const interval = setInterval(() => {
            useGameStore.getState().syncTacticalState();
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const handleDmSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!dmInput.trim() || isDMThinking) return;
        dmChat(dmInput);
        setDmInput("");
    };

    const activePlayer = entities.find(e => e.id === activePlayerId) || entities.find(e => e.type === 'player');

    return (
        <div className="flex h-screen bg-[#0f0f13] text-slate-200 font-sans select-none overflow-hidden">

            {/* SIDEBAR: NAVIGATION */}
            <div className="w-16 bg-[#050508]/90 backdrop-blur-xl border-r border-white/5 flex flex-col items-center py-6 gap-6 shadow-[20px_0_50px_rgba(0,0,0,0.3)] z-50">
                <div
                    onClick={() => setViewMode('PLAY')}
                    className={clsx(
                        "w-10 h-10 rounded-lg flex items-center justify-center transition-all cursor-pointer border group",
                        viewMode === 'PLAY'
                            ? "bg-gradient-to-br from-yellow-500 to-amber-700 shadow-[0_0_15px_rgba(245,158,11,0.3)] border-yellow-400/20"
                            : "bg-white/5 border-white/5 text-slate-500 hover:text-white"
                    )}
                >
                    <Sword size={22} className={clsx(viewMode === 'PLAY' ? "text-white" : "text-slate-500 group-hover:text-white")} />
                </div>

                <div
                    onClick={() => setViewMode('ARCHITECT')}
                    className={clsx(
                        "w-10 h-10 rounded-lg flex items-center justify-center transition-all cursor-pointer border group",
                        viewMode === 'ARCHITECT'
                            ? "bg-gradient-to-br from-yellow-500 to-amber-700 shadow-[0_0_15px_rgba(245,158,11,0.3)] border-yellow-400/20"
                            : "bg-white/5 border-white/5 text-slate-500 hover:text-white"
                    )}
                >
                    <Hammer size={22} className={clsx(viewMode === 'ARCHITECT' ? "text-white" : "text-slate-500 group-hover:text-white")} />
                </div>

                <div
                    onClick={() => setViewMode('BATTLE_LAB')}
                    className={clsx(
                        "w-10 h-10 rounded-lg flex items-center justify-center transition-all cursor-pointer border group",
                        viewMode === 'BATTLE_LAB'
                            ? "bg-gradient-to-br from-red-500 to-red-900 shadow-[0_0_15px_rgba(239,68,68,0.3)] border-red-400/20"
                            : "bg-white/5 border-white/5 text-slate-500 hover:text-white"
                    )}
                >
                    <LayoutGrid size={22} className={clsx(viewMode === 'BATTLE_LAB' ? "text-white" : "text-slate-500 group-hover:text-white")} />
                </div>

                <div className="w-8 h-px bg-white/5 my-2" />

                <button
                    onClick={() => setCharacterCreatorOpen(true)}
                    title="New Character"
                    className={clsx(
                        "p-2.5 rounded-xl transition-all",
                        isCharacterCreatorOpen ? "text-yellow-500 bg-white/5" : "text-green-500 hover:text-green-400 hover:bg-white/5"
                    )}
                >
                    <Sparkles size={22} />
                </button>
                <button
                    onClick={() => setCharacterSheetOpen(true)}
                    className={clsx(
                        "p-2.5 rounded-xl transition-all",
                        isCharacterSheetOpen ? "text-yellow-500 bg-white/5" : "text-slate-500 hover:text-yellow-500 hover:bg-white/5"
                    )}
                >
                    <User size={22} />
                </button>
                <button
                    onClick={() => setQuestLogOpen(true)}
                    className={clsx(
                        "p-2.5 rounded-xl transition-all",
                        isQuestLogOpen ? "text-yellow-500 bg-white/5" : "text-slate-500 hover:text-yellow-500 hover:bg-white/5"
                    )}
                >
                    <Scroll size={22} />
                </button>
                <button
                    onClick={() => setInventoryOpen(true)}
                    className={clsx(
                        "p-2.5 rounded-xl transition-all",
                        isInventoryOpen ? "text-yellow-500 bg-white/5" : "text-slate-500 hover:text-yellow-500 hover:bg-white/5"
                    )}
                >
                    <Shield size={22} />
                </button>
                <div className="flex-grow" />
                <button className="p-2.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-xl transition-all"><Terminal size={22} /></button>
            </div>

            {/* MAIN VIEWPORT */}
            <div className="flex-grow relative flex flex-col">
                {viewMode === 'PLAY' ? (
                    <>
                        {/* HUD: TOP BAR */}
                        <div className="h-20 border-b border-white/5 bg-[#050508]/40 backdrop-blur-xl flex items-center px-8 justify-between z-10">
                            <div className="flex flex-col gap-0.5">
                                <h1 className="text-xs font-black tracking-[0.3em] text-yellow-500/80 uppercase drop-shadow-[0_0_8px_rgba(234,179,8,0.3)]">
                                    {meta.title || "ESTABLISHING LINK..."}
                                </h1>
                                <p className="text-[10px] text-slate-400/60 uppercase font-black tracking-widest">{meta.description || "Synthesizing tactical data from SAGA Brain..."}</p>
                            </div>

                            {activePlayer && (
                                <div className="flex items-center justify-between w-full ml-12">

                                    {/* TURN ORDER TRACKER */}
                                    <div className="flex items-center gap-2">
                                        {turn_order && turn_order.map((t, idx) => {
                                            const ent = entities.find(e => e.id === t.entity_id);
                                            const isActive = t.entity_id === active_combatant;
                                            return (
                                                <div key={idx} className={clsx(
                                                    "px-3 py-1.5 rounded-full border text-[10px] font-black uppercase tracking-widest shadow-lg transition-all flex items-center gap-2",
                                                    isActive
                                                        ? "bg-yellow-500 text-black border-yellow-400 scale-110 z-10"
                                                        : "bg-black/50 text-slate-400 border-white/10"
                                                )}>
                                                    <div className={clsx(
                                                        "w-2 h-2 rounded-full",
                                                        t.faction === 'player' ? "bg-green-500" : "bg-red-500"
                                                    )} />
                                                    {ent ? ent.name : t.entity_id.split('-')[0]}
                                                </div>
                                            )
                                        })}
                                    </div>

                                    <div className="flex items-center gap-6 bg-[#12121a]/80 px-6 py-2.5 rounded-xl border border-white/5 shadow-2xl">
                                        <div className="text-right">
                                            <div className="text-[9px] font-black text-slate-500 uppercase tracking-tighter">Combat Vitality</div>
                                            <div className="text-sm font-black text-green-400 drop-shadow-[0_0_5px_rgba(74,222,128,0.3)]">{activePlayer.hp} / {activePlayer.maxHp} HP</div>
                                        </div>
                                        <div className="w-32 h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                            <div
                                                className="h-full bg-gradient-to-r from-green-600 via-green-400 to-green-500 animate-pulse"
                                                style={{ width: `${(activePlayer.hp / activePlayer.maxHp) * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>

                {/* ACTIVE QUEST HUD */}
                <QuestTracker />

                {/* MAP SETTINGS HUD */}
                <div className="absolute top-24 left-1/2 -translate-x-1/2 flex bg-black/60 p-1 rounded-xl border border-white/10 z-20 backdrop-blur-xl shadow-2xl">
                    <button
                        onClick={() => setPlayerMapView('TACTICAL')}
                        className={clsx(
                            "px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                            playerMapView === 'TACTICAL'
                                ? "bg-yellow-600/90 text-white shadow-lg"
                                : "text-slate-400 hover:text-white hover:bg-white/5"
                        )}
                    >
                        Battle Map
                    </button>
                    <button
                        onClick={() => {
                            if (!architectGrid) fetchArchitectGrid();
                            setPlayerMapView('WORLD');
                        }}
                        className={clsx(
                            "px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                            playerMapView === 'WORLD'
                                ? "bg-blue-600/90 text-white shadow-lg"
                                : "text-slate-400 hover:text-white hover:bg-white/5"
                        )}
                    >
                        World Map
                    </button>
                </div>

                {/* THE MAP DATA VIEW */}
                <div className="flex-grow overflow-auto flex items-center justify-center bg-[#0d0d12] p-12">
                    {playerMapView === 'TACTICAL' ? (
                        <MapCanvas
                            mapData={map}
                            entities={entities}
                            onCellClick={(x, y) => {
                                if (isDMThinking) return;
                                const clickedEntity = entities.find(e => e.pos[0] === x && e.pos[1] === y);
                                if (clickedEntity && clickedEntity.type === 'enemy') {
                                    dmChat(`I attack ${clickedEntity.name}`);
                                } else {
                                    dmChat(`I move to ${x}, ${y}`);
                                }
                            }}
                        />
                    ) : (
                        <MapCanvas
                            mapData={architectGrid || map}
                            entities={[{
                                id: 'player_marker', type: 'player', name: 'Party',
                                pos: meta.world_pos || [500, 500],
                                icon: 'sheet:115'
                            }]}
                            onCellClick={(x, y) => {
                                if (isDMThinking) return;
                                setPlayerMapView('TACTICAL');
                                dmChat(`We travel to world coordinates ${x}, ${y}`);
                            }}
                        />
                    )}
                </div>

                {/* MULTI-CHARACTER PARTY FRAMES */}
                {playerMapView === 'TACTICAL' && <PartyFrames />}

                {/* ACTION BAR (SKILLS/HUD) */}
                <ActionBar />

                {/* DM COMMAND BAR */}
                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                    <form
                        onSubmit={handleDmSubmit}
                        className="relative group"
                    >
                        <div className="absolute -inset-1 bg-gradient-to-r from-yellow-600/20 via-amber-600/30 to-yellow-600/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />

                        <div className="relative flex items-center bg-[#0a0a0f]/90 border border-white/10 backdrop-blur-2xl rounded-2xl p-1 shadow-2xl overflow-hidden">
                            <div className="flex items-center justify-center w-12 h-12 text-yellow-500 opacity-60">
                                {isDMThinking ? <Sparkles size={20} className="animate-spin" /> : <MessageSquare size={20} />}
                            </div>

                            <input
                                type="text"
                                value={dmInput}
                                onChange={(e) => setDmInput(e.target.value)}
                                placeholder={isDMThinking ? "The Oracle is synthesizing destiny..." : "Speak your intent to the Oracle..."}
                                className="flex-grow bg-transparent border-none outline-none text-sm placeholder:text-slate-600 px-2 py-4 font-medium tracking-tight disabled:opacity-50"
                                disabled={isDMThinking}
                            />

                            <button
                                type="submit"
                                disabled={isDMThinking || !dmInput.trim()}
                                className="px-6 py-3 bg-yellow-600/10 hover:bg-yellow-600 text-yellow-500 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 disabled:opacity-0"
                            >
                                Execute
                            </button>
                        </div>
                    </form>
                </div>

                <div className="absolute bottom-6 left-6 flex gap-2 z-50 pointer-events-auto">
                    <button onClick={() => fetchNewSession()} className="p-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/5 transition-colors"><Scroll size={16} className="text-slate-400" /></button>
                    <button onClick={() => submitResult('VICTORY')} className="px-4 py-2 bg-yellow-600/80 hover:bg-yellow-600 text-[10px] font-black uppercase tracking-tight rounded-lg border border-yellow-500/20 transition-all active:scale-95">Complete Objective</button>
                </div>

                {/* DRAWERS */}
                <CharacterSheet />
                <InventoryDrawer />
                <QuestLog />
            </>
            ) : viewMode === 'ARCHITECT' ? (
            <WorldArchitect />
            ) : (
            <TacticalCombat />
            )}
        </div>

            {/* ADVENTURE LOG (Chronicle) - Only in PLAY mode */ }
    {
        viewMode === 'PLAY' && (
            <div className="w-96 bg-[#050508]/95 backdrop-blur-2xl border-l border-white/5 flex flex-col shadow-[-20px_0_50px_rgba(0,0,0,0.4)]">
                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                            <Terminal size={14} className="text-yellow-500" />
                        </div>
                        <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-300">Chronicle</h2>
                    </div>
                </div>

                <div className="flex-grow p-6 overflow-y-auto space-y-4 font-mono text-[11px] custom-scrollbar">
                    {log.map((entry, i) => {
                        const isOracle = entry.includes("[THE ORACLE]");
                        const cleanEntry = entry.replace("[THE ORACLE] ", "");

                        return (
                            <div key={i} className={clsx(
                                "group animate-in fade-in slide-in-from-right-2 duration-500",
                                isOracle && "relative"
                            )}>
                                <div className={clsx(
                                    "flex items-start gap-3 leading-relaxed border-l pl-4 py-2 hover:bg-white/5 rounded-r-lg transition-colors",
                                    isOracle ? "border-yellow-500/40 bg-yellow-500/5 shadow-[inset_4px_0_10px_rgba(234,179,8,0.05)]" : "border-white/10"
                                )}>
                                    <div className={clsx(
                                        "mt-1 w-1 h-1 rounded-full px-0.5",
                                        isOracle ? "bg-yellow-500 shadow-[0_0_8px_#eab308]" : "bg-white/20 group-hover:bg-yellow-500"
                                    )} />
                                    <span className={clsx(
                                        "transition-colors",
                                        isOracle ? "text-amber-100 italic font-bold tracking-tight" : "text-slate-400 group-hover:text-slate-200 uppercase tracking-tight"
                                    )}>
                                        {cleanEntry}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="p-8 bg-gradient-to-t from-[#050508] to-transparent">
                    <p className="text-center text-[9px] font-bold text-slate-600 uppercase tracking-widest opacity-50">T.A.L.E.W.E.A.V.E.R.S. Session</p>
                </div>
            </div>
        )
    }

            <InventoryDrawer isOpen={isInventoryOpen} onClose={() => setInventoryOpen(false)} />
            <QuestLog isOpen={isQuestLogOpen} onClose={() => setQuestLogOpen(false)} />
        </div >
    );
}

export default App;
