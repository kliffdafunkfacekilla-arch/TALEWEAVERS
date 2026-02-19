# SAGA v2.0 Architecture Documentation

## 1. Overview
**SAGA (Simulator for AI-Generated Adventures)** is a next-generation TTRPG platform that combines a high-performance simulation engine with a reactive AI Dungeon Master.

**Version 2.0** marks a significant architectural shift from a procedural loops to a **State Machine Workflow** (LangGraph-inspired) and from DOM-based rendering to **WebGL/Canvas** (PixiJS).

## 2. Architecture Diagram

```mermaid
graph TD
    User[Player (VTT)] -->|HTTP POST /dm/action| Brain[SAGA Brain (FastAPI)]
    
    subgraph "SAGA Brain Workflow"
        Intent[1. Intent Node] -->|JSON| Lore[2. Lore Node]
        Lore -->|RAG + Context| Sim[3. Simulation Node]
        Sim -->|Mechanical Result| Narrative[4. Narrative Node]
    end
    
    subgraph "Vault Pipeline"
        Obsidian[Obsidian Vault (.md)] -->|Vault Compiler| SQLite
    end

    Brain -->|Workflow| Intent
    Narrative -->|Visual Updates + Text| User
    
    subgraph "Data Persistence"
        SQLite[(World State DB)]
        JSON[(Lore & Config)]
    end
    
    Sim -->|Read/Write| SQLite
    Lore -->|Read| JSON
```

## 3. Core Systems (Backend)

### 3.1. The Brain Workflow (`core/workflow/`)
The game loop is no longer a single monolithic function. It is a directed graph of specialized nodes:
- **IntentNode**: Uses `core/prompts/intent_resolver.txt` to translate natural language ("I attack the goblin") into structured JSON commands (`{"action": "ATTACK", "target": "Goblin"}`).
- **LoreNode**: Retrieves context relevant to the user's intent.
    - **RAG**: Searches `lore.json` for semantic matches.
    - **Memory**: Summarizes recent chat history to prevent context overflow.
- **SimNode**: Executes the mechanical rules.
    - **Combat**: Checks range, rolls dice, updates HP via the ECS.
    - **World**: Moving between graph nodes, triggering random encounters.
- **NarrativeNode**: Uses `core/prompts/narrative_dm.txt` to generate a visceral description of the outcome, weaving in the lore and mechanical results.

### 3.2. Entity Component System (ECS) (`core/core/ecs.py`)
Objects in the world are no longer hardcoded classes. They are flexible **Entities** composed of data **Components**.
- **Entity**: A unique ID container.
- **Components**:
    - `Position`: x, y, map_id
    - `Vitals`: hp, max_hp, sp, fp
    - `Stats`: Might, Reflexes, etc.
    - `Inventory`: List of items.
- **Legacy Adapter**: `LegacyCombatant` wraps the ECS to ensure older combat logic (which expects `self.hp`) continues to work by reading/writing to the `Vitals` component.

### 3.3. Persistence Layer (`core/core/database.py`)
- **SQLite**: The active world state (positions, health, inventory) is stored in `data/world_state.db`. This allows for millions of entities without the performance cost of parsing massive JSON files.
- **JSON**: Static data (Lore, Quests, Items) remains in JSON for human readability and easy editing.

### 3.4. Prompt Decoupling (`core/prompts/`)
AI personality and logic are defined in external text files, hot-reloadable without restarting the server:
- `intent_resolver.txt`: Rules for understanding player input.
- `narrative_dm.txt`: Style guide for the Dungeon Master response.

## 4. Visual Layer (Frontend)

### 4.1. PixiJS Canvas (`vtt/src/components/MapCanvas.tsx`)
The tactical map is rendered using **PixiJS** (WebGL), providing:
- **60+ FPS** even with hundreds of tokens and walls.
- **Dynamic Lighting** (future capability).
- **Smooth Animations** for movement and attacks.

### 4.2. Interactive Protocol
- **Click-to-Move**: Clicking a cell sends a natural language command ("I move to 15, 10") to the Brain.
- **State Sync**: The frontend polls `/tactical/state` or receives updates via the DM response to keep the visual state in sync with the ECS.

## 5. Development Guide

### 5.1. Directory Structure
```
TALEWEAVERS/
├── brain/
│   ├── server.py             # Main entry point (FastAPI)
│   └── combat/               # Legacy combat logic (migrating to ECS)
├── core/
│   ├── core/                 # Core systems (ECS, RAG, Database)
│   ├── workflow/             # The Brain's State Machine nodes
│   └── prompts/              # AI personality files
├── data/
│   ├── lore/                 # Atomic Knowledge Graph (Categories)
│   │   ├── biology/          # Species/Plants from Obsidian
│   │   ├── history/          # C++ Sim Historical Log
│   │   └── ...
│   └── world_state.db        # Active game save (SQLite)
└── vtt/                      # React + PixiJS Frontend
```

### 5.2. Running the Project
**Backend (Brain)**:
```bash
cd brain
python -m uvicorn server:app --reload
```
**Frontend (VTT)**:
```bash
cd vtt
npm run dev
```

## 6. Future Roadmap
- **Procedural Generation**: Hooking the `WorldGraph` into the `CampaignGenerator` for infinite world expansion.
- **Multi-Agent AI**: Giving NPCs their own `IntentNode` to plan independent goals.
- **3D View**: Potential upgrade to Three.js for a first-person perspective on the graph nodes.
