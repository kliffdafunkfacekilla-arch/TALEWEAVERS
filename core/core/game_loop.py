import json

class GameLoopController:
    """
    Orchestrates the transition between Macro (Sim), Meso (Quest), and Micro (Combat) layers.
    Bridges the Engine logic with the Sensory Layer (AI DM).
    """
    def __init__(self, chaos_manager, game_state, sensory_layer):
        self.chaos = chaos_manager
        self.state = game_state
        self.sensory = sensory_layer
        
        # UI/State Helpers
        self.scene_stack = type('SceneStack', (object,), {
            'stack': [], 
            'total_steps': 10, 
            'quest_title': "The Unbroken World"
        })()
        self.active_scene = type('Scene', (object,), {'text': "You stand at the threshold of destiny."})()
        self.player_combatant = None
        
        # Interaction Engine
        self.interaction = type('Interaction', (object,), {'oracle': sensory_layer})()

    def load_player(self):
        """Loads player data into the active loop."""
        p_data = self.state.get_player()
        print(f"[LOOP] Player '{p_data['Name']}' loaded.")

    def get_state(self):
        """Returns the current loop state for the UI/CLI."""
        return {
            "mode": "exploration",
            "chaos": self.chaos.chaos_level,
            "scene": self.active_scene.text
        }

    def handle_action(self, action, x=None, y=None, **kwargs):
        """Processes a player action and queries the AI DM for narrative feedback."""
        self.chaos.increment_chaos(0.02)
        
        # Let the AI DM perceive the action
        narrative = self.sensory.chat(f"Player performs action: {action}. Describe the result.")
        self.active_scene.text = narrative
        return narrative

    def start_campaign(self, biome="Dungeon", quest_type="Exploration"):
        """Initializes a new campaign session."""
        log = [f"Venturing into the {biome}..."]
        narrative = self.sensory.chat(f"The party enters a {biome} for a {quest_type} quest. Describe the opening.")
        self.active_scene.text = narrative
        log.append(narrative)
        return log
