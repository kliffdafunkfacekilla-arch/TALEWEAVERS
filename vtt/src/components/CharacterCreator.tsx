import React, { useState, useEffect } from 'react';
import { useGameStore } from '../store';
import { ChevronRight, ChevronLeft, Shield, Sword, Sparkles, User, Save } from 'lucide-react';

export function CharacterCreator() {
    const { isCharacterCreatorOpen, setCharacterCreatorOpen, fetchNewSession } = useGameStore();

    const [step, setStep] = useState(1);
    const [speciesList, setSpeciesList] = useState<any[]>([]);
    const [schoolsList, setSchoolsList] = useState<any>({});
    const [triadsList, setTriadsList] = useState<any>({});
    const [matrixData, setMatrixData] = useState<any>({});
    const [backstoryData, setBackstoryData] = useState<any>({});
    const [evolutionFlavor, setEvolutionFlavor] = useState<any>({});
    const [itemsList, setItemsList] = useState<any>({});

    // Character State
    const [charName, setCharName] = useState("");
    const [selectedSpecies, setSelectedSpecies] = useState<any>(null);
    const [selectedLoadout, setSelectedLoadout] = useState<{ weapon: string | null, armor: string | null }>({ weapon: null, armor: null });
    const [selections, setSelections] = useState<Record<string, { mind: string | null, body: string | null }>>({
        HEAD: { mind: null, body: null },
        BODY: { mind: null, body: null },
        ARMS: { mind: null, body: null },
        LEGS: { mind: null, body: null },
        SKIN: { mind: null, body: null },
        SPECIAL: { mind: null, body: null }
    });

    // Phase 16 Narrative State
    const [currentScenarioIndex, setCurrentScenarioIndex] = useState(0);
    const [backstorySelections, setBackstorySelections] = useState<any[]>([]);
    const [tempSelection, setTempSelection] = useState<any>(null); // { triad: string, discipline: string, stat: string }

    const [selectedSchool, setSelectedSchool] = useState<string | null>(null);

    // Fetch initial Data
    useEffect(() => {
        if (!isCharacterCreatorOpen) return;
        fetch('/api/creator/data')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    setSpeciesList(data.species);
                    setSchoolsList(data.schools);
                    setTriadsList(data.triads);
                    setMatrixData(data.evolution);
                    setBackstoryData(data.backstory);
                    setEvolutionFlavor(data.evolution_flavor);
                    setItemsList(data.items);
                }
            })
            .catch(err => console.error("Failed fetching creator data", err));
    }, [isCharacterCreatorOpen]);

    if (!isCharacterCreatorOpen) return null;

    // Derived State Computations
    const currentStats = () => {
        if (!selectedSpecies) return {};
        const stats = { ...selectedSpecies.base_stats };

        // Phase 2: Matrix Bumps (+1 for each selection)
        Object.values(selections).forEach(sel => {
            if (sel.mind) stats[sel.mind] = (stats[sel.mind] || 0) + 1;
            if (sel.body) stats[sel.body] = (stats[sel.body] || 0) + 1;
        });

        // Phase 16: Narrative Backstory Bumps (+1 to selected stat per pick)
        backstorySelections.forEach(sel => {
            if (sel.stat) stats[sel.stat] = (stats[sel.stat] || 0) + 1;
        });

        return stats;
    };

    // Derived Vitals (Phase 14 Formulas)
    const derivedHP = () => {
        const stats = currentStats();
        return 10 + (stats.Fortitude || 0) + (stats.Vitality || 0);
    };
    const derivedCMP = () => {
        const stats = currentStats();
        return 10 + (stats.Willpower || 0) + (stats.Intuition || 0);
    };
    const derivedSP = () => {
        const stats = currentStats();
        return (stats.Endurance || 0) + (stats.Might || 0);
    };
    const derivedFP = () => {
        const stats = currentStats();
        return (stats.Knowledge || 0) + (stats.Logic || 0);
    };

    const getTraitName = (slot: string, mind: string | null, body: string | null) => {
        if (!mind || !body || !selectedSpecies) return "Mutation";
        const kingdom = selectedSpecies.species.toUpperCase();
        const flavor = evolutionFlavor[kingdom];
        if (!flavor) return matrixData[slot]?.matrix[mind]?.[body]?.name || "Mutation";

        const noun = flavor.nouns[slot]?.[mind] || mind;
        const adj = flavor.adjectives[body] || body;
        return `${adj} ${noun}`;
    };

    const getTraitMechanic = (slot: string, mind: string | null, body: string | null) => {
        if (!mind || !body) return "";
        return matrixData[slot]?.matrix[mind]?.[body]?.mechanic || "";
    };

    const handleTriadToggle = (triadName: string) => {
        if (selectedTriads.includes(triadName)) {
            setSelectedTriads(selectedTriads.filter(t => t !== triadName));
        } else if (selectedTriads.length < 3) {
            setSelectedTriads([...selectedTriads, triadName]);
        }
    };



    const handleLoadoutSelect = (slot: string, optionName: string) => {
        setLoadout({ ...loadout, [slot]: optionName });
    };

    const handleFinalize = async () => {
        const payload = {
            Name: charName || "Nameless Hero",
            Species: selectedSpecies.species.toUpperCase(),
            Level: 1,
            Stats: currentStats(),
            Loadout: {
                ...Object.entries(selections).reduce((acc: any, [slot, sel]) => {
                    const matrixName = getTraitName(slot, sel.mind, sel.body);
                    acc[slot] = matrixName;
                    return acc;
                }, {}),
                Equipment: selectedLoadout
            },
            Triads: backstorySelections.map(s => s.triad),
            Backstory: backstorySelections.map(s => `${s.discipline} (as a ${s.triad})`).join(", "),
            School: selectedSchool || "None",
            Traits: Object.entries(selections).reduce((acc: any, [slot, sel]) => {
                acc[slot] = getTraitMechanic(slot, sel.mind, sel.body);
                return acc;
            }, {}),
            HP: derivedHP(),
            CMP: derivedCMP(),
            Stamina: derivedSP(),
            Focus: derivedFP()
        };

        try {
            const res = await fetch('/api/creator/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.status === 'success') {
                setCharacterCreatorOpen(false);
                // We'll hard fetch the session, we'll configure tactical.py to prioritize the newest save next...
                await fetchNewSession(payload.Name);
            }
        } catch (e) {
            console.error("Save failed", e);
        }
    };


    return (
        <div className="fixed inset-0 z-50 bg-slate-900/95 flex items-center justify-center p-8 backdrop-blur-md">
            <div className="bg-slate-800 border-2 border-slate-700 rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden">

                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
                    <div className="flex items-center gap-3">
                        <User className="text-yellow-500" />
                        <h1 className="text-xl font-bold uppercase tracking-widest text-white">Character Architect</h1>
                    </div>
                    <div className="flex gap-2">
                        {[1, 2, 3, 4, 5, 6].map(s => (
                            <div key={s} className={`h-2 w-12 rounded-full ${s <= step ? 'bg-yellow-500' : 'bg-white/10'}`} />
                        ))}
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-8 relative">

                    {/* STEP 1: SPECIES */}
                    {step === 1 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <h2 className="text-2xl font-bold text-white mb-6">Select Biological Origin</h2>
                            <div className="grid grid-cols-3 gap-6">
                                {speciesList.map((sp) => (
                                    <div
                                        key={sp.species}
                                        onClick={() => setSelectedSpecies(sp)}
                                        className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${selectedSpecies?.species === sp.species ? 'border-yellow-500 bg-yellow-500/10' : 'border-slate-700 bg-slate-800/50 hover:border-slate-500'}`}
                                    >
                                        <h3 className="text-xl font-bold uppercase tracking-wider text-slate-200 mb-2">{sp.species}</h3>
                                        <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                                            <div>Might: <span className="text-white">{sp.base_stats.Might}</span></div>
                                            <div>Endurance: <span className="text-white">{sp.base_stats.Endurance}</span></div>
                                            <div>Reflexes: <span className="text-white">{sp.base_stats.Reflexes}</span></div>
                                            <div>Awareness: <span className="text-white">{sp.base_stats.Awareness}</span></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* STEP 2: EVOLUTION MATRIX */}
                    {step === 2 && selectedSpecies && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <h2 className="text-2xl font-bold text-white mb-2">Configure {selectedSpecies.species} Evolution</h2>
                            <p className="text-slate-400 mb-6 text-sm">Select one Mind and one Body stat for each physiological slot. No stat can be reused.</p>

                            <div className="space-y-6">
                                {Object.entries(matrixData).map(([slot, data]: [string, any]) => {
                                    const usedMind = Object.entries(selections).filter(([s, v]) => s !== slot && v.mind).map(([s, v]) => v.mind);
                                    const usedBody = Object.entries(selections).filter(([s, v]) => s !== slot && v.body).map(([s, v]) => v.body);
                                    const currentSelection = selections[slot];

                                    return (
                                        <div key={slot} className="bg-black/20 p-4 rounded-lg border border-white/5 flex flex-col md:flex-row gap-6 items-center">
                                            <div className="md:w-32">
                                                <h3 className="text-xs font-bold uppercase tracking-widest text-yellow-500">{slot}</h3>
                                                <div className="text-[10px] text-slate-500">{data.label}</div>
                                            </div>

                                            <div className="flex-1 flex gap-4">
                                                {/* Mind Stats Selector */}
                                                <div className="flex-1">
                                                    <div className="text-[9px] uppercase text-slate-600 mb-1">Mind Stat</div>
                                                    <div className="grid grid-cols-3 gap-1">
                                                        {data.mind_stats.map((s: string) => {
                                                            const usedMind = Object.entries(selections)
                                                                .filter(([key]) => key !== slot)
                                                                .map(([, val]) => val.mind);
                                                            return (
                                                                <button
                                                                    key={s}
                                                                    disabled={usedMind.includes(s)}
                                                                    onClick={() => setSelections({ ...selections, [slot]: { ...currentSelection, mind: s } })}
                                                                    className={`px-2 py-1.5 rounded text-[10px] font-bold transition-all border ${currentSelection.mind === s ? 'bg-blue-500/30 border-blue-400 text-white' : usedMind.includes(s) ? 'bg-slate-900 border-slate-800 text-slate-700 cursor-not-allowed opacity-30' : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'}`}
                                                                >
                                                                    {s.slice(0, 5)}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>

                                                <div className="flex items-center text-slate-600 px-2">×</div>

                                                {/* Body Stats Selector */}
                                                <div className="flex-1">
                                                    <div className="text-[9px] uppercase text-slate-600 mb-1">Body Stat</div>
                                                    <div className="grid grid-cols-3 gap-1">
                                                        {data.body_stats.map((s: string) => {
                                                            const usedBody = Object.entries(selections)
                                                                .filter(([key]) => key !== slot)
                                                                .map(([, val]) => val.body);
                                                            return (
                                                                <button
                                                                    key={s}
                                                                    disabled={usedBody.includes(s)}
                                                                    onClick={() => setSelections({ ...selections, [slot]: { ...currentSelection, body: s } })}
                                                                    className={`px-2 py-1.5 rounded text-[10px] font-bold transition-all border ${currentSelection.body === s ? 'bg-red-500/30 border-red-400 text-white' : usedBody.includes(s) ? 'bg-slate-900 border-slate-800 text-slate-700 cursor-not-allowed opacity-30' : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'}`}
                                                                >
                                                                    {s.slice(0, 5)}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="md:w-64 bg-black/40 p-3 rounded border border-white/5 flex flex-col justify-center items-center">
                                                <div className="text-[9px] uppercase text-slate-600">Trait Formed</div>
                                                <div className="text-white font-bold text-xs text-center line-clamp-1 mb-1">
                                                    {currentSelection.mind && currentSelection.body ? (
                                                        getTraitName(slot, currentSelection.mind, currentSelection.body)
                                                    ) : (
                                                        <span className="text-slate-700 italic">Incomplete</span>
                                                    )}
                                                </div>
                                                <div className="text-[9px] text-slate-500 text-center leading-tight">
                                                    {currentSelection.mind && currentSelection.body ? (
                                                        <div className="text-yellow-500/80 font-medium">
                                                            {getTraitMechanic(slot, currentSelection.mind, currentSelection.body)}
                                                        </div>
                                                    ) : null}
                                                    {currentSelection.mind && currentSelection.body ? (
                                                        <div className="mt-1 opacity-50">
                                                            {slot === "HEAD" || slot === "ARMS" ? data.descriptions[currentSelection.mind] : data.descriptions[currentSelection.body]}
                                                        </div>
                                                    ) : null}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* STEP 3: NARRATIVE BACKSTORY */}
                    {step === 3 && backstoryData?.stages && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="flex justify-between items-end mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-white mb-2">{backstoryData.stages[currentScenarioIndex].label}</h2>
                                    <p className="text-slate-400 text-sm">Step {currentScenarioIndex + 1} of 8: Shaping your history.</p>
                                </div>
                                <div className="text-blue-500 font-mono text-xl font-bold">
                                    {(currentScenarioIndex / 8 * 100).toFixed(0)}% Complete
                                </div>
                            </div>

                            {/* Narrative Bridge */}
                            <div className="bg-blue-500/5 border-l-4 border-blue-500 p-4 mb-8 italic text-slate-300 text-sm">
                                {currentScenarioIndex === 0
                                    ? backstoryData.context_intro[backstoryData.stages[0].id]
                                    : `Because you chose to be ${backstorySelections[currentScenarioIndex - 1].discipline}, ${backstoryData.context_intro[backstoryData.stages[currentScenarioIndex].id]}`
                                }
                            </div>

                            <p className="text-white text-lg mb-8 leading-relaxed font-serif">
                                "{backstoryData.stages[currentScenarioIndex].prompt}"
                            </p>

                            <div className="grid grid-cols-2 gap-4">
                                {backstoryData.stages[currentScenarioIndex].groups.map((groupName: string) => {
                                    const triad = triadsList[groupName];
                                    if (!triad) return null;
                                    return triad.disciplines.map((d: any) => (
                                        <div
                                            key={`${groupName}-${d.name}`}
                                            onClick={() => setTempSelection({ triad: groupName, discipline: d.name, stats: d.stats })}
                                            className={`p-4 rounded-xl border cursor-pointer transition-all ${tempSelection?.discipline === d.name ? 'border-yellow-500 bg-yellow-500/10' : 'border-slate-800 bg-slate-800/20 hover:border-slate-600'}`}
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <h4 className="font-bold text-slate-200">{d.name}</h4>
                                                <span className="text-[9px] uppercase tracking-tighter text-slate-600 bg-black/40 px-2 py-0.5 rounded">{groupName}</span>
                                            </div>

                                            {tempSelection?.discipline === d.name && (
                                                <div className="mt-4 animate-in fade-in slide-in-from-top-2">
                                                    <p className="text-[10px] uppercase text-slate-500 mb-2">Choose which attribute to hone:</p>
                                                    <div className="flex gap-2">
                                                        {d.stats.map((s: string) => (
                                                            <button
                                                                key={s}
                                                                onClick={(e) => { e.stopPropagation(); setTempSelection({ ...tempSelection, stat: s }); }}
                                                                className={`flex-1 py-1 px-2 rounded text-[10px] font-bold border ${tempSelection.stat === s ? 'bg-yellow-500 border-yellow-400 text-black' : 'bg-slate-700 border-slate-600 text-slate-300'}`}
                                                            >
                                                                +1 {s}
                                                            </button>
                                                        ))}
                                                    </div>
                                                    {tempSelection.stat && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                const newSels = [...backstorySelections];
                                                                newSels[currentScenarioIndex] = tempSelection;
                                                                setBackstorySelections(newSels);
                                                                if (currentScenarioIndex < 7) {
                                                                    setCurrentScenarioIndex(currentScenarioIndex + 1);
                                                                    setTempSelection(null);
                                                                } else {
                                                                    setStep(4);
                                                                }
                                                            }}
                                                            className="w-full mt-4 bg-yellow-600 hover:bg-yellow-500 text-black py-2 rounded font-black text-xs uppercase tracking-widest"
                                                        >
                                                            Lock In Decision
                                                        </button>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ));
                                })}
                            </div>
                        </div>
                    )}

                    {/* STEP 4: SCHOOLS OF POWER */}
                    {step === 4 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <h2 className="text-2xl font-bold text-white mb-2">Select Arcane/Martial Path</h2>
                            <p className="text-slate-400 mb-6 text-sm">Prerequisite: Matching Attribute must be 10 or higher.</p>
                            <div className="grid grid-cols-3 gap-6">
                                {Object.entries(schoolsList).map(([schoolName, data]: any) => {
                                    const stats = currentStats();
                                    const hasPrereq = (stats[data.attribute] || 0) >= 10;
                                    return (
                                        <div
                                            key={schoolName}
                                            onClick={() => hasPrereq && setSelectedSchool(schoolName)}
                                            className={`p-6 rounded-xl border-2 transition-all ${hasPrereq ? 'cursor-pointer hover:border-slate-500' : 'opacity-40 grayscale cursor-not-allowed border-red-900/20'} ${selectedSchool === schoolName ? 'border-purple-500 bg-purple-500/10' : 'border-slate-700 bg-slate-800/50'}`}
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="text-xl font-bold uppercase tracking-wider text-purple-400">{schoolName}</h3>
                                                {!hasPrereq && <span className="text-[9px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30">LOCKED</span>}
                                            </div>
                                            <p className="text-sm text-slate-400 mb-3">Attribute: <span className={hasPrereq ? 'text-green-400' : 'text-red-400'}>{data.attribute} ({stats[data.attribute] || 0})</span></p>
                                            <div className="text-xs text-slate-300 space-y-1">
                                                <div className="font-bold text-slate-500">Tier 1 Spells:</div>
                                                {data.spells.filter((s: any) => s.tier === 1).map((s: any) => (
                                                    <div key={s.name}>• {s.name} ({s.type})</div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* STEP 5: LOADOUT SELECTION */}
                    {step === 5 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <h2 className="text-2xl font-bold text-white mb-2">Select Starting Equipment</h2>
                            <p className="text-slate-400 mb-6 text-sm">Your training in {backstorySelections.map(s => s.triad).join(", ")} dictates your available gear.</p>

                            <div className="grid grid-cols-2 gap-8">
                                {/* Weapons */}
                                <div className="space-y-4">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-yellow-500 border-b border-yellow-500/20 pb-2">Primary Weapon</h3>
                                    <div className="grid grid-cols-1 gap-2">
                                        {Object.entries(itemsList.WEAPON?.types || {}).filter(([_, item]: any) =>
                                            backstorySelections.some(s => s.triad === item.triad_group)
                                        ).map(([name, item]: any) => (
                                            <div
                                                key={name}
                                                onClick={() => setSelectedLoadout({ ...selectedLoadout, weapon: name })}
                                                className={`p-4 rounded border-2 transition-all cursor-pointer ${selectedLoadout.weapon === name ? 'border-yellow-500 bg-yellow-500/10' : 'border-slate-700 bg-slate-800/50 hover:border-slate-500'}`}
                                            >
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="font-bold text-white text-sm">{name}</span>
                                                    <span className="text-[10px] text-yellow-500/70 font-bold">{item.triad_group}</span>
                                                </div>
                                                <div className="flex gap-3 text-[10px] text-slate-400">
                                                    <span>Dmg: <span className="text-white">{item.dmg}</span></span>
                                                    <span>Cost: <span className="text-white">{item.cost}</span></span>
                                                    <span>Prop: <span className="text-white">{item.prop}</span></span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Armor */}
                                <div className="space-y-4">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-blue-500 border-b border-blue-500/20 pb-2">Defensive Gear</h3>
                                    <div className="grid grid-cols-1 gap-2">
                                        {Object.entries(itemsList.ARMOR?.types || {}).filter(([_, item]: any) =>
                                            backstorySelections.some(s => s.triad === item.triad_group)
                                        ).map(([name, item]: any) => (
                                            <div
                                                key={name}
                                                onClick={() => setSelectedLoadout({ ...selectedLoadout, armor: name })}
                                                className={`p-4 rounded border-2 transition-all cursor-pointer ${selectedLoadout.armor === name ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 bg-slate-800/50 hover:border-slate-500'}`}
                                            >
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="font-bold text-white text-sm">{name}</span>
                                                    <span className="text-[10px] text-blue-500/70 font-bold">{item.triad_group}</span>
                                                </div>
                                                <div className="flex gap-3 text-[10px] text-slate-400">
                                                    <span>Prot: <span className="text-white">-{item.prot} Dmg</span></span>
                                                    <span>Cost: <span className="text-white">{item.cost}</span></span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* STEP 6: FINALIZE */}
                    {step === 6 && selectedSpecies && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300 flex flex-col items-center justify-center h-full">
                            <Sparkles className="w-16 h-16 text-yellow-500 mb-6" />
                            <h2 className="text-4xl font-black uppercase tracking-[0.2em] text-white mb-8">Forge Destiny</h2>

                            <div className="w-full max-w-2xl space-y-4">
                                <div>
                                    <label className="block text-xs font-bold uppercase text-slate-400 mb-2 text-center">Hero Name</label>
                                    <input
                                        type="text"
                                        value={charName}
                                        onChange={(e) => setCharName(e.target.value)}
                                        placeholder="Enter name..."
                                        className="w-full bg-black/40 border border-white/20 rounded p-4 text-white text-xl text-center placeholder:text-slate-600 focus:outline-none focus:border-yellow-500"
                                    />
                                </div>

                                <div className="bg-black/20 border border-white/10 rounded-lg p-6 mt-6 grid grid-cols-2 gap-6">
                                    <div className="space-y-4">
                                        <h3 className="text-sm font-bold uppercase text-slate-500 border-b border-white/5 pb-2">Vitals & Origin</h3>
                                        <div className="grid grid-cols-1 gap-2 text-sm">
                                            <div><span className="text-slate-400">Species:</span> <span className="text-white font-bold ml-2">{selectedSpecies.species}</span></div>
                                            <div><span className="text-slate-400">School:</span> <span className="text-purple-400 font-bold ml-2">{selectedSchool || 'None'}</span></div>
                                            <div><span className="text-slate-400">Loadout:</span> <span className="text-yellow-500 font-bold ml-2">{selectedLoadout.weapon} & {selectedLoadout.armor}</span></div>
                                            <div className="flex gap-4 mt-2">
                                                <div><span className="text-slate-400 text-xs uppercase">HP</span> <div className="text-red-400 font-black text-xl">{derivedHP()}</div></div>
                                                <div><span className="text-slate-400 text-xs uppercase">CMP</span> <div className="text-blue-400 font-black text-xl">{derivedCMP()}</div></div>
                                                <div><span className="text-slate-400 text-xs uppercase">SP</span> <div className="text-yellow-400 font-black text-xl">{derivedSP()}</div></div>
                                                <div><span className="text-slate-400 text-xs uppercase">FP</span> <div className="text-green-400 font-black text-xl">{derivedFP()}</div></div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h3 className="text-sm font-bold uppercase text-slate-500 border-b border-white/5 pb-2">Traits & Training</h3>
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Physiological Evolution</span>
                                            <div className="flex gap-1 flex-wrap mb-4">
                                                {Object.entries(selections).map(([slot, sel]) => (
                                                    <span key={slot} className="px-2 py-0.5 bg-yellow-500/10 border border-yellow-500/20 text-yellow-500/70 rounded text-[9px]">
                                                        {getTraitName(slot, sel.mind, sel.body)}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Biographical Path</span>
                                            <p className="text-[10px] text-slate-400 leading-relaxed italic border-l border-yellow-500/30 pl-3">
                                                {backstorySelections.map((sel, i) => (
                                                    <span key={i}>
                                                        {i === 0 ? "" : " "}
                                                        You were known for being <span className="text-yellow-500/80">{sel.discipline}</span> in your youth, which led to your study of <span className="text-blue-400/80">{sel.triad}</span>.
                                                    </span>
                                                ))}
                                                {selectedSchool && <span> This path eventually led you to the sacred arts of <span className="text-purple-400 font-bold">{selectedSchool}</span>.</span>}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer Controls */}
                <div className="p-4 border-t border-white/10 bg-black/40 flex justify-between items-center">
                    <button
                        onClick={() => setStep(Math.max(1, step - 1))}
                        disabled={step === 1}
                        className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold uppercase text-sm transition-all ${step === 1 ? 'opacity-0 cursor-default' : 'bg-slate-700 hover:bg-slate-600 text-white'}`}
                    >
                        <ChevronLeft size={16} /> Back
                    </button>

                    {step < 6 ? (
                        <button
                            onClick={() => setStep(step + 1)}
                            disabled={
                                (step === 1 && !selectedSpecies) ||
                                (step === 2 && Object.values(selections).some(v => v.mind === null || v.body === null)) ||
                                (step === 3 && backstorySelections.length < 8) ||
                                (step === 4 && !selectedSchool) ||
                                (step === 5 && (!selectedLoadout.weapon || !selectedLoadout.armor))
                            }
                            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold uppercase text-sm transition-all ${((step === 1 && !selectedSpecies) ||
                                (step === 2 && Object.values(selections).some(v => v.mind === null || v.body === null)) ||
                                (step === 3 && backstorySelections.length < 8) ||
                                (step === 4 && !selectedSchool) ||
                                (step === 5 && (!selectedLoadout.weapon || !selectedLoadout.armor)))
                                ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                                : 'bg-yellow-600 hover:bg-yellow-500 text-black'
                                }`}
                        >
                            Next <ChevronRight size={16} />
                        </button>
                    ) : (
                        <button
                            onClick={handleFinalize}
                            disabled={!charName.trim()}
                            className={`flex items-center gap-2 px-8 py-3 rounded-lg font-black uppercase text-sm tracking-wider shadow-[0_0_15px_rgba(234,179,8,0.3)] transition-all ${!charName.trim() ? 'opacity-50 grayscale cursor-not-allowed' : 'bg-yellow-500 hover:bg-yellow-400 hover:scale-105 text-black'}`}
                        >
                            <Save size={16} /> Save & Enter World
                        </button>
                    )}
                </div>

            </div>
        </div>
    );
}
