from .graph_runtime import WorkflowNode, GraphState
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from core.systems.social_combat import social_engine
from core.systems.interaction_engine import InteractionEngine

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
        raw_intent = self.sensory.resolve_intent(
            state.user_input, 
            state.player_data,
            environment_context=state.environment_context
        )
        
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
    def __init__(self, combat_provider=None, simulation_manager=None, quest_manager=None, campaign_gen=None, graph_manager=None):
        self.get_combat = combat_provider if callable(combat_provider) else (lambda: combat_provider)
        self.sim = simulation_manager
        self.quests = quest_manager
        self.campaign_gen = campaign_gen
        self.graph = graph_manager

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
                target = state.intent.get('target')
                if self.graph and target:
                    # Graph Travel
                    current_node = self.graph.find_nearest_node(player_pos[0], player_pos[1])
                    if current_node:
                        neighbors = self.graph.get_neighbors(current_node['id'])
                        destination = None
                        
                        # Check graph neighbors
                        for n in neighbors:
                            if target.lower() in str(n['id']).lower() or target.lower() in current_node.get('name', '').lower():
                                destination = n
                                break
                                
                        if destination:
                            # Actually find the node's coordinates
                            dest_node = next((node for node in self.graph.nodes if str(node['id']) == str(destination['id'])), None)
                            if dest_node:
                                state.player_data['pos'] = (dest_node['x'], dest_node['y'])
                                travel_time = int(destination.get('weight', 10) / 10)
                                self.sim.advance_time(travel_time, state.player_data['pos'])
                                result = f"You travel along the trade route to {dest_node.get('name', dest_node['id'])}. The journey takes {travel_time} hours."
                            else:
                                result = f"You cannot find the path to {target}."
                        else:
                            result = f"There is no known route to {target} from here."
                    else:
                        result = f"You are lost in the wilds, off the main graph."
                else:
                    # Local tactical coordinate travel fallback
                    params = state.intent.get('parameters', {})
                    dx, dy = params.get('dx', 0), params.get('dy', 0)
                    new_x = player_pos[0] + dx
                    new_y = player_pos[1] + dy
                    state.player_data['pos'] = (new_x, new_y)
                    result = f"You travel through the wilds towards ({new_x}, {new_y})."
                updates.append({'type': 'MOVE_PLAYER', 'pos': [new_x, new_y]})
            elif action == 'TALK':
                print(f"[NODE] Routing Intent '{action}' to Social Engine")
                result, updates = social_engine.resolve_social_action(state.intent, state.player_data)
            elif action in ['INTERACT', 'USE']:
                target = state.intent.get('target', 'nothing')
                
                # 1. Rules-Engine Execution (Strict Determinism)
                mech_result, mech_updates = InteractionEngine.resolve_interaction(state.intent, state.player_data)
                result = mech_result
                updates.extend(mech_updates)
                
                # 2. Check Narrative Quest seeds (Side effect of interaction)
                if self.campaign_gen and self.campaign_gen.current_campaign:
                    # Target might be passed by the LLM as 'poi_path_...' or just its name
                    for poi in self.campaign_gen.current_campaign.pois:
                        if target.lower() in poi.id.lower() or target.lower() in poi.description.lower() or target.lower() in poi.type.lower():
                            side_q = self.campaign_gen.trigger_side_quest(poi.id)
                            if side_q:
                                result += f" [QUEST DISCOVERED: {side_q.title} - {side_q.description}]"
                            break

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
