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
            "stream": False,
            "format": "json" # FORCE JSON OUTPUT
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "{}")
            return f"Error: Ollama returned {response.status_code}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"

    def _load_prompt(self, filename, fallback=""):
        try:
            path = os.path.join(os.path.dirname(__file__), "prompts", filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except:
            pass
        return fallback

    def generate_narrative(self, action_result, world_context, persona="Dark & Visceral"):
        """Generates the DM's narrative response."""
        system_prompt = self._load_prompt("narrative_dm.txt", "You are the SAGA Oracle.")
        
        # Build context
        context_str = f"WORLD_STATE: {world_context.get('chaos', 'Stable')}\n"
        if world_context.get('active_quests'):
            context_str += f"ACTIVE_QUESTS: {json.dumps(world_context['active_quests'])}\n"
        if world_context.get('lore'):
            context_str += f"LORE: {world_context['lore']}\n"
        if world_context.get('history'):
            context_str += f"HISTORY:\n{world_context['history']}\n"

        full_prompt = f"{context_str}\nSIM_RESULT: {action_result}\nDescribe this result narratively."
        
        # Narrative doesn't need 'json' format, so we use a raw chat or change payload
        # For narrative, ideally we want text, but we set format='json' in chat() above.
        # Let's add a parameter to chat() to toggle format.
        return self._chat_raw(full_prompt, system_prompt=system_prompt)

    def _chat_raw(self, prompt, system_prompt):
        """Helper for non-JSON text responses."""
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "system": system_prompt, "stream": False}
        try:
            r = requests.post(url, json=payload, timeout=30)
            return r.json().get("response", "The oracle is silent.")
        except:
            return "Connection Failed."

    def resolve_intent(self, user_input, character_context, environment_context=None):
        """
        Translates player natural language into a structured JSON action.
        Aligned with the PlayerIntent Pydantic model.
        """
        system_prompt = self._load_prompt("intent_resolver.txt", "Extract action from input.")
        
        # Add schema hint
        schema_hint = """
        Output MUST be valid JSON matching this schema:
        {
          "action": "ATTACK" | "MOVE" | "SEARCH" | "TALK" | "INTERACT" | "USE" | "REST" | "SKILL" | "ITEM",
          "target": string | null (The target entity ID or name),
          "item_id": string | null (If ITEM, the item ID, e.g. 'potion_hp_minor'),
          "skill_id": string | null (If SKILL, the skill ID, e.g. 'FIREBALL'),
          "parameters": { "dx": int, "dy": int, ... },
          "narrative_flavor": "Short description of the action"
        }
        """
        
        env_str = ""
        if environment_context:
            env_str = f"ENVIRONMENT_TAGS (Interactive Objects Nearby): {json.dumps(environment_context)}\n"
            schema_hint += "\nNote: You can target objects in the ENVIRONMENT_TAGS. If they have tags like 'breakable', 'openable', etc., your action should logically interact with them."
        
        prompt = f"CHARACTER_STATE: {json.dumps(character_context)}\n{env_str}USER_INPUT: '{user_input}'\n{schema_hint}\nRESOLVE INTENT:"
        
        response = self.chat(prompt, system_prompt=system_prompt)
        try:
            return json.loads(response)
        except:
            print(f"[DEBUG] Raw Intent Response: {response}")
            return {"action": "TALK", "narrative_flavor": "mumbling", "parameters": {}}
