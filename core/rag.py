import json
import os
import re

class SimpleRAG:
    """
    Lightweight Retrieval-Augmented Generation for Lore.
    Currently uses an optimized keyword-weighting index while 
    preparing for a full vector embedding migration.
    """
    def __init__(self, lore_data, async_init=False):
        self.lore = lore_data
        self.index = {}
        self.is_ready = False
        
        if async_init:
            import threading
            threading.Thread(target=self._initialize, daemon=True).start()
        else:
            self._initialize()

    def _initialize(self):
        """Builds the index and marks the engine as ready."""
        print("[RAG] Indexing Lore data...")
        self.index = self._build_index()
        self.is_ready = True
        print(f"[RAG] Indexing complete. {len(self.index)} terms mapped.")

    def _build_index(self):
        index = {}
        # Handle if lore is a list of dicts or a single dict
        entries = self.lore.items() if isinstance(self.lore, dict) else enumerate(self.lore)
        
        for key, entry in entries:
            # Extract content text from dict or use entry directly if string
            text = entry.get('content', '') if isinstance(entry, dict) else str(entry)
            entry_id = entry.get('id', key) if isinstance(entry, dict) else key
            
            # Basic tokenization
            words = set(re.findall(r'\w+', text.lower()))
            for word in words:
                if word not in index:
                    index[word] = []
                index[word].append(entry_id)
        return index

    def search(self, query, top_k=3):
        """Finds most relevant lore entries for a query."""
        if not self.is_ready:
            return "Lore database is currently indexing... please wait a moment."
            
        query_words = re.findall(r'\w+', query.lower())
        scores = {}
        
        # Mapping to retrieve original entry by ID
        entry_map = { (str(e.get('id', i)) if isinstance(e, dict) else str(i)): e 
                      for i, e in (enumerate(self.lore) if isinstance(self.lore, list) else self.lore.items()) }

        for word in query_words:
            if word in self.index:
                for entry_id in self.index[word]:
                    scores[str(entry_id)] = scores.get(str(entry_id), 0) + 1
                    
        # Sort by score
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for entry_id, score in sorted_ids[:top_k]:
            entry = entry_map.get(entry_id)
            if entry:
                content = entry.get('content', str(entry)) if isinstance(entry, dict) else str(entry)
                results.append(content)
            
        return "\n---\n".join(results) if results else "No relevant lore found."
