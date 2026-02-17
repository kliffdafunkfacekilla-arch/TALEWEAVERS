# TALEWEAVERS: SAGA Simulation Architecture

This document outlines the multi-tiered simulation logic used to separate high-level world events from low-level tactical combat.

## 1. Simulation Tiers (Hierarchical Separation)

| Tier | Name | Focus | Data Structure | Time Scale | Implementation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 3** | **Global (Macro)** | Factions, Borders, Wars, History | **Graph** | Monthly/Weekly | `gamestate.json` |
| **Tier 2** | **Regional (Meso)** | Trade Roads, Caravans, Plot Points | **Vector Graph** | Daily | `campaign_system.py` |
| **Tier 1** | **Tactical (Micro)** | Combat, Movement, Interacting | **Grid** | Hourly/Turns | `mechanics.py` |

---

## 2. Graph vs. Grid Logic

### The Graph (World Level)
The world simulation operates on a **Non-Euclidean Graph**.
- **Nodes**: Known settlements, lore sites, and faction capitals.
- **Edges**: Political relationships and trade routes.
- **Why?**: Influence and supply chains aren't strictly limited by physical distance; a secure trade road (Graph Edge) is faster than a short walk through a dangerous forest.

### The Grid (Encounters)
The moment a player interacts with a specific point, the engine "collapses" the simulation into a **Spatial Grid**.
- **Structure**: A 2D array (usually 20x20 to 50x50).
- **Function**: Handles tactical positioning, line-of-sight, and range.
- **Why?**: Mechanics like *Flanking*, *Cover*, and *Aura Effects* require precise coordinate math that graph nodes cannot provide.

---

## 3. Data Flow & Translation

When the player moves from World Travel (Graph) to Combat (Grid):
1. **Context Extraction**: The server queries the Global Graph for the nearest faction influence and biome data.
2. **State Injection**: This context (e.g., "The Iron Caldera controls this pass") influences grid generation (e.g., adding Iron-clad guards to the enemy list).
3. **Feedback Loop**: Combat results (Grid) are summarized and fed back into the Graph (e.g., a Bandit death reduces the "Chaos Factor" of that node in `gamestate.json`).

## 4. Focal Point Simulation (LOD)

To maximize performance, the simulation uses a **Level of Detail (LOD)** strategy. Detail is concentrated where the player is located, and abstracted elsewhere.

| Depth Layer | Radius | Simulation Logic | Performance Cost |
| :--- | :--- | :--- | :--- |
| **Tactical** | 0 - 50 | Full entity ticking, physics, per-item logic. | **High** |
| **Local** | 51 - 250 | Node-level trade, local growth, POI spawning. | **Medium** |
| **Regional** | 251 - 750 | Statistical influence, faction-level resource shifts. | **Low** |
| **Global** | 750+ | Macro-trends only (World Age, Global Pop). | **Minimal** |

### Lazy Ticking
Nodes and regions outside the player's immediate Focal Point use "Lazy Ticking". They only recalculate their state when:
1.  The player enters their radius (Catching up on missed ticks statistically).
2.  A Monthly/Global tick occurs.

---

## 5. Time Ticking (`SimulationManager`)

- **Hourly Tick**: Focal Point Only. Restores resources and triggers local NPC behaviors.
- **Daily Tick**: Local Circle. Advances local trade and campaign story seeds.
- **Weekly Tick**: Regional Circle. Updates faction power and influence.
- **Monthly Tick**: Global (Entire World). Epoch-level changes and macro-trends.
