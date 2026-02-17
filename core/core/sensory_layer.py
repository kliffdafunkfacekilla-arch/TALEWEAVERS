import json
import requests
import sys

class SensoryLayer:
    """
    Local AI Gateway using Ollama (Qwen 2.5).
    Acts as the 'Sense' through which the AI DM perceives the simulation.
    """
    def __init__(self, model="qwen2.5:latest", host="http://localhost:11434"):
        self.model = model
        self.host = host
        self.is_active = True

    def chat(self, prompt, system_prompt="You are the S.A.G.A. Oracle, a neutral AI DM."):
        if not self.is_active:
            return "Sensory Layer Offline."
            
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "No response.")
            return f"Error: Ollama returned {response.status_code}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"

    def perceive_event(self, event_type, data):
        """Converts raw simulation data into a narrative prompt."""
        prompt = f"SIM_EVENT: {event_type}\nDATA: {json.dumps(data)}\nDescribe this event narratively to the player."
        return self.chat(prompt)

    def generate_narrative(self, action_result, world_context, persona="Dark & Visceral"):
        """
        The 'Prompt Sandwich' logic with Quest Awareness (Deep Sight).
        """
        # 1. BOTTOM: Context (Lore & World State & Quests)
        bottom = f"WORLD_STATE: {world_context.get('chaos', 'Stable')}\n"
        
        if world_context.get('active_quests'):
            bottom += f"ACTIVE_QUESTS: {json.dumps(world_context['active_quests'])}\n"
            
        if world_context.get('visible_objects'):
            bottom += f"VISIBLE_OBJECTS: {json.dumps(world_context['visible_objects'])}\n"

        if world_context.get('lore'):
            bottom += f"LORE_RELEVANCE: {world_context['lore']}\n"
            
        # 2. MEAT: Simulation Result
        meat = f"SIM_RESULT: {action_result}\n"
        
        # 3. TOP: Persona & Formatting
        top = f"PERSONA: {persona}\nCONSTRAINT: 2-3 sentences. Focus on sensory details and quest relevance. No internal monologue."
        
        full_prompt = f"{bottom}\n{meat}\n{top}"
        return self.chat(full_prompt)
    def resolve_intent(self, user_input, character_context):
        """
        Translates player natural language into an engine action.
        Returns JSON: {"action": "MOVE|ATTACK|SEARCH|TALK|WAIT", "target": "...", "parameters": {...}}
        """
        system_prompt = """
        You are the T.A.L.E.W.E.A.V.E.R.S. Intent Resolver. 
        Your job is to translate player chat into structured engine commands.
        VALID ACTIONS:
        - MOVE: Travel (params: dx, dy)
        - ATTACK: Combat (target: enemy name)
        - SEARCH: Look for items/secrets
        - TALK: Interact with NPC
        - WAIT: Advance time
        
        OUTPUT FORMAT: JSON ONLY.
        """
        
        prompt = f"CHARACTER_STATE: {json.dumps(character_context)}\nUSER_INPUT: '{user_input}'\nRESOLVE INTENT:"
        
        response = self.chat(prompt, system_prompt=system_prompt)
        try:
            # Attempt to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            return {"action": "TALK", "text": response} # Fallback to just talking
        except:
            return {"action": "TALK", "text": response}
