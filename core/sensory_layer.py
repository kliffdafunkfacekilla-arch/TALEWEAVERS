import json
import requests
import sys
import os

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

    def _load_prompt(self, filename, fallback=""):
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "prompts", filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except:
            pass
        return fallback

    def generate_narrative(self, action_result, world_context, persona="Dark & Visceral"):
        """
        The 'Prompt Sandwich' logic with Quest Awareness (Deep Sight).
        """
        system_prompt = self._load_prompt("narrative_dm.txt", "You are the SAGA Oracle.")
        
        # 1. BOTTOM: Context (Lore & World State & Quests)
        bottom = f"WORLD_STATE: {world_context.get('chaos', 'Stable')}\n"
        
        if world_context.get('active_quests'):
            bottom += f"ACTIVE_QUESTS: {json.dumps(world_context['active_quests'])}\n"
            
        if world_context.get('visible_objects'):
            bottom += f"VISIBLE_OBJECTS: {json.dumps(world_context['visible_objects'])}\n"

        if world_context.get('lore'):
            bottom += f"LORE_RELEVANCE: {world_context['lore']}\n"
            
        if world_context.get('history'):
            bottom += f"ADVENTURE_CONTEXT:\n{world_context['history']}\n"

        # 2. MEAT: Simulation Result
        meat = f"SIM_RESULT: {action_result}\n"
        
        full_prompt = f"{bottom}\n{meat}"
        return self.chat(full_prompt, system_prompt=system_prompt)

    def resolve_intent(self, user_input, character_context):
        """
        Translates player natural language into an engine action.
        """
        system_prompt = self._load_prompt("intent_resolver.txt", "Extract action from input.")
        
        prompt = f"CHARACTER_STATE: {json.dumps(character_context)}\nUSER_INPUT: '{user_input}'\nRESOLVE INTENT:"
        
        response = self.chat(prompt, system_prompt=system_prompt)
        try:
            # Strip markdown code blocks if present
            clean_response = response.replace("```json", "").replace("```", "").strip()
            
            # Attempt to extract JSON from response
            start = clean_response.find("{")
            end = clean_response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(clean_response[start:end])
            return {"action": "TALK", "text": response} # Fallback to just talking
        except:
            return {"action": "TALK", "text": response}
