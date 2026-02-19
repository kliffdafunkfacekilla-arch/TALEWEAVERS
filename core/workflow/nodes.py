from .graph_runtime import WorkflowNode, GraphState
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

class PlayerIntent(BaseModel):
    """Structured representation of player action from natural language."""
    action: Literal["ATTACK", "MOVE", "SEARCH", "TALK", "INTERACT", "USE", "REST"]
    target: Optional[str] = Field(None, description="The name of the character or object being targeted")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Metadata like dx, dy, or specific item names")
    narrative_flavor: str = Field(..., description="A short description of HOW the player performed the action")

class IntentNode(WorkflowNode):
    """
    Step 1: Parse the user's intent using Pydantic enforcement.
    """
    def __init__(self, sensory_layer):
        self.sensory = sensory_layer

    def run(self, state: GraphState) -> GraphState:
        print(f"[NODE] Parsing Intent: '{state.user_input}'")
        
        # Use sensory layer to get structured intent
        # The sensory layer should now return a PlayerIntent object or dict matching it
        raw_intent = self.sensory.resolve_intent(state.user_input, state.player_data)
        
        # Enforce Pydantic validation
        if isinstance(raw_intent, dict):
            try:
                intent_obj = PlayerIntent(**raw_intent)
                state.intent = intent_obj.model_dump()
            except Exception as e:
                print(f"[ERROR] Intent Validation Failed: {e}. Falling back to TALK.")
                state.intent = PlayerIntent(action="TALK", narrative_flavor="confused mumbling").model_dump()
        else:
            state.intent = raw_intent # Assume already validated if produced by sensory
            
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
    def __init__(self, combat_provider=None, simulation_manager=None, quest_manager=None):
        self.get_combat = combat_provider if callable(combat_provider) else (lambda: combat_provider)
        self.sim = simulation_manager
        self.quests = quest_manager

    def run(self, state: GraphState) -> GraphState:
        combat_engine = self.get_combat()
        action = state.intent.get('action', 'TALK')
        
        updates: List[Dict[str, Any]] = []
        result = "Nothing happens."

        player_pos = state.player_data.get('pos', (500, 500))

        # ADVANCE WORLD TIME (1 hour per action)
        if self.sim:
            self.sim.advance_time(1, player_pos)

        # MECHANICS ROUTING
        if combat_engine and combat_engine.active:
            print(f"[NODE] Routing Intent '{action}' to CombatEngine")
            result, updates = combat_engine.process_intent(state.intent)
        
        # WORLD LOGIC fallback
        elif self.sim:
            if action in ['MOVE', 'TRAVEL']:
                params = state.intent.get('parameters', {})
                dx, dy = params.get('dx', 0), params.get('dy', 0)
                new_x = player_pos[0] + dx
                new_y = player_pos[1] + dy
                state.player_data['pos'] = (new_x, new_y)
                result = f"You travel through the wilds towards ({new_x}, {new_y})."
                updates.append({'type': 'MOVE_PLAYER', 'pos': [new_x, new_y]})
            else:
                result = f"Action {action} performed. The world continues to turn."

        # QUEST TRACKING
        if self.quests and action:
            quest_updates = self.quests.update_objective(action.lower(), 1)
            if quest_updates:
                result += " " + " ".join(quest_updates)

        state.mechanical_result = result
        state.visual_updates = updates
        return state

class NarrativeNode(WorkflowNode):
    """
    Step 4: Generate the DM's response.
    """
    def __init__(self, sensory_layer, quest_manager=None):
        self.sensory = sensory_layer
        self.quests = quest_manager

    def run(self, state: GraphState) -> GraphState:
        context = {
            "chaos": state.world_meta.get("chaos_level", 0.5),
            "position": state.player_data.get("pos", [500, 500]),
            "intent": state.intent,
            "lore": state.lore_context,
            "history": state.history_context,
            "active_quests": self.quests.get_active_quests() if self.quests else []
        }
        
        response = self.sensory.generate_narrative(
            action_result=state.mechanical_result,
            world_context=context,
            persona="The Oracle: Visceral and Direct"
        )
        
        state.narrative_response = response
        return state
