import json
import os

class MemoryManager:
    """
    Handles long-term conversation memory and summarization.
    Prevents context window saturation by flushing raw history into distilled summaries.
    """
    def __init__(self, sensory_layer, history_limit=20):
        self.sensory = sensory_layer
        self.history_limit = history_limit
        self.history = []
        self.summary = ""

    def add_interaction(self, user_prompt, ai_response):
        """Adds a turn to history and triggers summarization if limit reached."""
        self.history.append({"user": user_prompt, "ai": ai_response})
        
        if len(self.history) >= self.history_limit:
            self._summarize()

    def _summarize(self):
        """Uses the AI to distill history into a single narrative summary."""
        if not self.history:
            return

        text_to_summarize = "\n".join([f"Player: {h['user']}\nOracle: {h['ai']}" for h in self.history])
        
        prompt = f"Existing Summary: {self.summary}\n\nRecent Events:\n{text_to_summarize}\n\nDistill the above into a concise chronological summary of our adventure so far. Focus on key plot points and character status."
        
        new_summary = self.sensory.chat(prompt, system_prompt="You are a chronicler. Summarize the following events into a single dense paragraph.")
        
        if "Connection Failed" not in new_summary:
            self.summary = new_summary
            self.history = [] # Flush history after summarizing
            print(f"[MEMORY] History summarized. New Summary Length: {len(self.summary)}")

    def get_full_context(self):
        """Returns the summary plus any recent active history."""
        context = f"ADVENTURE_SUMMARY: {self.summary}\n"
        if self.history:
            recent = "\n".join([f"Player: {h['user']}\nOracle: {h['ai']}" for h in self.history])
            context += f"RECENT_HISTORY:\n{recent}"
        return context
