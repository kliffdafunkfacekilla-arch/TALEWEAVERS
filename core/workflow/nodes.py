from .graph_runtime import WorkflowNode, GraphState
from typing import Dict, Any, List

class IntentNode(WorkflowNode):
    """
    Step 1: Parse the user's intent.
    """
    def __init__(self, sensory_layer):
        self.sensory = sensory_layer

    def run(self, state: GraphState) -> GraphState:
        # Resolve natural language into structured JSON action
        print(f"[NODE] Parsing Intent: '{state.user_input}'")
        intent_json = self.sensory.resolve_intent(state.user_input, state.player_data)
        state.intent = intent_json
        return state

class LoreNode(WorkflowNode):
    """
    Step 2: Retrieve context (RAG + Memory).
    """
    def __init__(self, rag_engine=None, memory_manager=None):
        self.rag = rag_engine
        self.memory = memory_manager

    def run(self, state: GraphState) -> GraphState:
        # Retrieve relevant semantic lore
        if self.rag:
            print(f"[NODE] Fetching Lore for '{state.user_input}'")
            state.lore_context = self.rag.search(state.user_input)
        
        # Retrieve recent conversation history
        if self.memory:
            state.history_context = self.memory.get_full_context()
            
        return state

class SimNode(WorkflowNode):
    """
    Step 3: Execute mechanical logic (Movement, Combat, etc).
    """
    def __init__(self, combat_provider=None, simulation_manager=None):
        self.get_combat = combat_provider if callable(combat_provider) else (lambda: combat_provider)
        self.sim = simulation_manager

    def run(self, state: GraphState) -> GraphState:
        combat_engine = self.get_combat()
        action = state.intent.get('action', 'TALK')
        cmd = state.intent.get('parameters', {})
        target_name = state.intent.get('target', '')
        
        updates: List[Dict[str, Any]] = []
        result = "Nothing happens."

        # COMBAT LOGIC (Grid Mode)
        if combat_engine and combat_engine.active:
            player = next((c for c in combat_engine.combatants if c.name == "player_burt"), None)
            
            if action == 'MOVE' and player:
                dx, dy = cmd.get('dx', 0), cmd.get('dy', 0)
                ok, msg = combat_engine.move_char(player, player.x + dx, player.y + dy)
                result = msg
                if ok:
                    updates.append({'type': 'MOVE_TOKEN', 'id': player.name, 'pos': [player.x, player.y]})
            
            elif action == 'ATTACK' and player:
                target = next((c for c in combat_engine.combatants if target_name.lower() in c.name.lower()), None)
                if target:
                    log = combat_engine.attack_target(player, target)
                    result = " ".join(log)
                    updates.append({'type': 'PLAY_ANIMATION', 'name': 'MELEE', 'target': target.name})
                    updates.append({'type': 'UPDATE_HP', 'id': target.name, 'hp': target.hp})
                else:
                    result = "You swing at the air."

        # WORLD LOGIC (Graph Mode)
        elif self.sim:
            # Fallback to narrative simulation
            result = f"You traverse the world. {action} executed."

        state.mechanical_result = result
        state.visual_updates = updates
        return state

class NarrativeNode(WorkflowNode):
    """
    Step 4: Generate the DM's response.
    """
    def __init__(self, sensory_layer):
        self.sensory = sensory_layer

    def run(self, state: GraphState) -> GraphState:
        # Construct context object for the sensory layer
        context = {
            "chaos": state.world_meta.get("chaos_level", 0.5),
            "position": state.player_data.get("pos", [500, 500]),
            "intent": state.intent,
            "lore": state.lore_context,
            "history": state.history_context,
            "active_quests": []  # Placeholder
        }
        
        print(f"[NODE] Generating Narrative based on result: '{state.mechanical_result}'")
        response = self.sensory.generate_narrative(
            action_result=state.mechanical_result,
            world_context=context,
            persona="The Oracle: Visceral and Direct"
        )
        
        state.narrative_response = response
        return state
