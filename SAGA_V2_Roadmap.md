# TALEWEAVERS: Next-Gen Architecture Plan (SAGA v2)

This document outlines the strategic pivot for TALEWEAVERS to maximize performance, scalability, and AI intelligence.

## 1. World Simulation: The "Graph-First" Model 🕸️
**Current**: Hybrid Grid-Graph but still relies on coordinate math for world updates.  
**Target**: Purely Non-Euclidean Graph for the "World Logic."

- **Nodes**: Settlements, Dungeons, Resource Points, Biome Hubs.
- **Edges**: Travel routes with "Weights" (Time/Danger/Distance).
- **Simulation**: Events trigger on Nodes ("Famine in Town X") and propagate through Edges to neighbors.
- **VTT Bridge**: The Grid only exists as a "View" when needed. The Brain operates only on the Knowledge Graph.

## 2. Intelligence: LangGraph State Machine 🧠
**Current**: FastAPI endpoints and procedural loops.  
**Target**: Cyclic State Machine using LangGraph.

- **The Cycle**: `Input -> Analyze Intent -> Retrieve Lore (RAG) -> Update Simulation State -> Generate Narrative -> Output`.
- **Persistence**: Automate turn-based checkpoints for "Time Travel" (Replay/Debug).
- **Control**: Cleanly separate "Narrative Logic" from "Mechanical Math."

## 3. Storage & Retrieval: RAG + SQLite 🗄️
**Current**: Massive `gamestate.json` and linear `lore.json` scans.  
**Target**: Relational Persistence and Semantic Retrieval.

- **Lore RAG**: Set up a local vector store (ChromaDB). Chunk lore entries and use semantic search instead of keyword matching.
- **SQLite Engine**: Move active game state (Entities, Factions, World Nodes) to SQLite. This prevents JSON corruption and allows complex relational queries (e.g., "Find all nodes controlled by faction X within 2 edges of the player").
- **Summarization Loop**: Implement a history buffer that summarizes chat logs once they exceed 20 turns, keeping a stable context window.

## 4. Systems: ECS Migration (Entity Component System) 🛠️
**Current**: Rigid Class Hierarchies (`character.py`, `item.py`).  
**Target**: Composition over Inheritance.

- **Entity**: A simple UUID.
- **Components**: `Position`, `Inventory`, `Stats`, `Actor`, `Renderable`.
- **Systems**: The "Brain" and "Combat" systems iterate over entities with relevant components. This makes "Talking Swords" or "Sentient Towns" trivial to implement.

## 5. Frontend: Canvas/PixiJS Rendering 🎨
**Current**: React DOM nodes for the grid.  
**Target**: Hardware-accelerated Canvas.

- **Rendering Layer**: Switch `MapGrid` to HTML5 `<canvas>` or PixiJS. This allows maps of 1000x1000 tiles without browser lag.
- **Texture Atlases**: Consolidate individual PNGs in `public/tiles` into texture sheets to reduce HTTP overhead.

---

## 🏗️ Phased Implementation Plan

### Phase 1: The Database & Memory (Foundations)
1.  **SQLite Implementation**: Migrate `db.gamestate` to SQLite tables.
2.  **RAG Pipeline**: Implement ChromaDB for `lore.json`.
3.  **Summarization System**: Add the narrative buffer to `CampaignGenerator`.

### Phase 2: The Graph & ECS (Logic)
1.  **World Graph Factory**: Convert `gamestate.json` nodes into a weighted graph.
2.  **ECS Refactor**: Separate character data into components. Remove deep class inheritance.
3.  **LangGraph Integration**: Wrap `dm/action` in a cycle.

### Phase 3: The View (Performance)
1.  **Canvas Migration**: Rewrite `MapGrid.tsx` using PixiJS.
2.  **Texture Batching**: Generate atlases for existing assets.

### Phase 4: Prompt Decoupling
1.  Move all SAGA prompts to `core/prompts/*.yaml`.
2.  Implement a dynamic prompt loader.
