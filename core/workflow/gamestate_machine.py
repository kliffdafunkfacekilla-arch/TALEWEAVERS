from .graph_runtime import GraphRuntime, GraphState
from .nodes import IntentNode, LoreNode, SimNode, NarrativeNode

class SagaGameLoop:
    """
    The orchestrator that wires together the SAGA Brain workflow.
    Uses the LangGraph pattern: Input -> Intent -> Lore -> Sim -> Narrative -> Output.
    """
    def __init__(self, sensory_layer, combat_engine, rag_engine, memory_manager):
        self.runtime = GraphRuntime()
        
        # 1. Parse Node
        self.runtime.add_node("intent", IntentNode(sensory_layer))
        
        # 2. Lore Retrieval Node
        self.runtime.add_node("lore", LoreNode(rag_engine, memory_manager))
        
        # 3. Simulation Logic Node
        # TODO: Pass the full SimulationManager here for world-level updates
        self.runtime.add_node("simulation", SimNode(combat_engine))
        
        # 4. DM Narrative Node
        self.runtime.add_node("narrative", NarrativeNode(sensory_layer))

    def process_turn(self, user_input, context):
        """
        Executes a single game turn through the graph.
        Returns the final state.
        """
        initial_state = GraphState(
            user_input=user_input,
            player_data=context.get('player', {}),
            world_meta=context.get('meta', {})
        )
        
        final_state = self.runtime.execute(initial_state)
        
        return {
            "narrative": final_state.narrative_response,
            "visual_updates": final_state.visual_updates,
            "mechanical_log": final_state.mechanical_result,
            "intent": final_state.intent
        }
