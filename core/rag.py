import json
import os
import chromadb
import frontmatter

class SimpleRAG:
    """
    Retrieval-Augmented Generation for Lore using ChromaDB Vector Store.
    Migrated from legacy RegEx keyword matching to true Semantic Embeddings.
    """
    def __init__(self, data_path=None, lore_data=None, async_init=False):
        self.data_path = data_path
        self.lore = lore_data or {}
        self.is_ready = False
        
        # Initialize Vector Store
        db_path = os.path.join(data_path, ".chroma") if data_path else "./data/.chroma"
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="saga_lore")
        
        if async_init:
            import threading
            threading.Thread(target=self._initialize, daemon=True).start()
        else:
            self._initialize()

    def _initialize(self):
        """Builds the vector embeddings from directory or data dict."""
        print("[RAG] Initializing ChromaDB Vector Store...")
        
        if self.data_path and os.path.exists(self.data_path):
            self._load_from_directory(self.data_path)
        elif self.lore:
            # Fallback for legacy monolithic lore.json
            self._load_from_dict()
            
        self.is_ready = True
        print(f"[RAG] ChromaDB initialization complete. {self.collection.count()} vectors mapped.")

    def _load_from_directory(self, root_path):
        """Recursively loads atomic JSON lore files and upserts to Chroma."""
        docs, metas, ids = [], [], []
        
        for root, dirs, files in os.walk(root_path):
            for file in files:
                filepath = os.path.join(root, file)
                if file.endswith('.md'):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            post = frontmatter.load(f)
                            e_id = post.get("id", file)
                            self.lore[e_id] = post.metadata
                            content = post.content
                            tags = ",".join(post.get('tags', []))
                            nodes_str = ",".join(post.get('associated_nodes', []))
                            docs.append(content)
                            ids.append(e_id)
                            metas.append({
                                "tags": tags,
                                "associated_nodes": nodes_str,
                                "importance": post.get('importance', 0.5)
                            })
                    except Exception as e:
                        print(f"[RAG] Error parsing markdown {file}: {e}")
                elif file.endswith('.json'):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            entry = json.load(f)
                            e_id = entry.get('id', file)
                            self.lore[e_id] = entry
                            
                            content = entry.get('content', entry.get('narrative', str(entry))) if isinstance(entry, dict) else str(entry)
                            tags = ",".join(entry.get('tags', [])) if isinstance(entry, dict) else ""
                            nodes_str = ",".join(entry.get('associated_nodes', [])) if 'associated_nodes' in entry else ""
                            
                            docs.append(content)
                            ids.append(e_id)
                            metas.append({
                                "tags": tags,
                                "associated_nodes": nodes_str,
                                "importance": entry.get('importance', 0.5) if isinstance(entry, dict) else 0.5
                            })
                    except Exception as e:
                        print(f"[RAG] Error loading json {file}: {e}")
                        
        self._upsert_batches(docs, metas, ids)

    def _load_from_dict(self):
        docs, metas, ids = [], [], []
        for e_id, entry in self.lore.items():
            content = entry.get('content', entry.get('narrative', str(entry))) if isinstance(entry, dict) else str(entry)
            docs.append(content)
            ids.append(str(e_id))
            metas.append({"type": "legacy_import"})
        self._upsert_batches(docs, metas, ids)

    def _upsert_batches(self, docs, metas, ids):
        if not docs: return
        batch_size = 100
        for i in range(0, len(docs), batch_size):
            self.collection.upsert(
                documents=docs[i:i+batch_size],
                metadatas=metas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

    def search(self, query, top_k=3, loc_id=None, mode="vector"):
        """
        Semantic Search via ChromaDB.
        """
        if not self.is_ready:
            return "Lore database is currently indexing into ChromaDB... please wait a moment."
            
        # Enrich the semantic context if spatial filtering is requested
        if loc_id:
            query = f"{query} near {loc_id}"

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        if not results['documents'] or not len(results['documents'][0]):
            return "No relevant lore found."
            
        return "\n---\n".join(results['documents'][0])
