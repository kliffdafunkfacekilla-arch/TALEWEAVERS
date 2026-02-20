from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class GraphState(BaseModel):
    """
    The shared state passed between nodes in the workflow.
    Allows for deterministic time-travel and debugging.
    """
    # 1. Inputs
    user_input: str
    player_data: Dict[str, Any]
    world_meta: Dict[str, Any]
    environment_context: List[Dict[str, Any]] = []
    
    # 2. Intermediate Products
    intent: Optional[Dict[str, Any]] = None
    lore_context: str = ""
    history_context: str = ""
    
    # 3. Mechanical Outcomes (Deterministic)
    mechanical_result: str = ""
    visual_updates: List[Dict[str, Any]] = []
    
    # 4. Final Output
    narrative_response: str = ""
    error: Optional[str] = None

class WorkflowNode:
    """Base class for a processing step."""
    def run(self, state: GraphState) -> GraphState:
        raise NotImplementedError

class GraphRuntime:
    """
    Manages the execution flow: input -> parse -> logic -> narrative -> output.
    """
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.sequence: List[str] = []

    def add_node(self, name: str, node: WorkflowNode):
        self.nodes[name] = node
        self.sequence.append(name)

    def execute(self, initial_state: GraphState) -> GraphState:
        """Executes the workflow graph (linear for now)."""
        current_state = initial_state
        print(f"[GRAPH] Starting Workflow with input: '{current_state.user_input}'")
        
        for node_name in self.sequence:
            try:
                print(f"[GRAPH] Executing Node: {node_name}")
                node = self.nodes[node_name]
                current_state = node.run(current_state)
                
                if current_state.error:
                    print(f"[GRAPH] Error in {node_name}: {current_state.error}")
                    break
            except Exception as e:
                import traceback
                traceback.print_exc()
                current_state.error = str(e)
                break
                
        return current_state
