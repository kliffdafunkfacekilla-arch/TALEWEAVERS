import json
import os
import re

class SimpleRAG:
    """
    Lightweight Retrieval-Augmented Generation for Lore.
    Currently uses an optimized keyword-weighting index while 
    preparing for a full vector embedding migration.
    """
    def __init__(self, data_path=None, lore_data=None, async_init=False):
        self.data_path = data_path
        self.lore = lore_data or {}
        self.index = {}
        self.spatial_index = {} # loc_id -> [entry_ids]
        self.is_ready = False
        
        if async_init:
            import threading
            threading.Thread(target=self._initialize, daemon=True).start()
        else:
            self._initialize()

    def _initialize(self):
        """Builds the index from directory or data dict."""
        print("[RAG] Initializing Knowledge Graph...")
        
        # Load atomic lore pieces from directory if provided
        if self.data_path and os.path.exists(self.data_path):
            self._load_from_directory(self.data_path)
            
        self.index = self._build_index()
        self.is_ready = True
        print(f"[RAG] Indexing complete. {len(self.index)} terms and {len(self.spatial_index)} spatial nodes mapped.")

    def _load_from_directory(self, root_path):
        """Recursively loads atomic JSON lore files."""
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith('.json'):
                    try:
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            entry = json.load(f)
                            e_id = entry.get('id', file)
                            self.lore[e_id] = entry
                            
                            # Build spatial index
                            nodes = entry.get('associated_nodes', [])
                            for node in nodes:
                                if node not in self.spatial_index:
                                    self.spatial_index[node] = []
                                self.spatial_index[node].append(e_id)
                    except Exception as e:
                        print(f"[RAG] Error loading {file}: {e}")

    def _build_index(self):
        index = {}
        for entry_id, entry in self.lore.items():
            text = entry.get('content', '') if isinstance(entry, dict) else str(entry)
            tags = " ".join(entry.get('tags', [])) if isinstance(entry, dict) else ""
            full_text = f"{text} {tags}".lower()
            
            words = set(re.findall(r'\w+', full_text))
            for word in words:
                if word not in index:
                    index[word] = []
                index[word].append(entry_id)
        return index

    def search(self, query, top_k=3, loc_id=None, mode="hybrid"):
        """
        Finds most relevant lore entries.
        Modes: 'keyword', 'vector' (semantic), 'hybrid' (combined)
        loc_id: Optional spatial context (e.g. 'node_12') to prioritize local lore.
        """
        if not self.is_ready:
            return "Lore database is currently indexing... please wait a moment."
            
        keyword_results = self._keyword_search(query, top_k, loc_id)
        
        return keyword_results

    def _keyword_search(self, query, top_k=3, loc_id=None):
        query_words = re.findall(r'\w+', query.lower())
        scores = {}
        
        # 1. Spatial Priority (Direct Hit)
        if loc_id and loc_id in self.spatial_index:
            for entry_id in self.spatial_index[loc_id]:
                scores[str(entry_id)] = scores.get(str(entry_id), 0) + 5.0 # Large boost

        # 2. Semantic/Keyword Scoring
        for word in query_words:
            if word in self.index:
                for entry_id in self.index[word]:
                    scores[str(entry_id)] = scores.get(str(entry_id), 0) + 1.0
                    
        # Sort by score and importance (Requirement Checklist 2)
        def get_importance(eid):
            entry = self.lore.get(eid)
            return entry.get('importance', 0.5) if isinstance(entry, dict) else 0.5

        sorted_ids = sorted(scores.items(), key=lambda x: (x[1] * get_importance(x[0])), reverse=True)
        
        results = []
        for entry_id, score in sorted_ids[:top_k]:
            entry = entry_map.get(entry_id)
            if entry:
                content = entry.get('content', entry.get('narrative', str(entry))) if isinstance(entry, dict) else str(entry)
                results.append(content)
            
        return "\n---\n".join(results) if results else "No relevant lore found."

    def vector_search(self, query_vector, top_k=5):
        """
        Placeholder for true semantic search.
        Requires embeddings for the lore entries.
        """
        pass
