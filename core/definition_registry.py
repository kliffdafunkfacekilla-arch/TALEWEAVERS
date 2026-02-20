import os
import json
from typing import Dict, Any, Type, TypeVar
from pydantic import BaseModel

from core.models.definitions import (
    ResourceDefinition, 
    SpeciesDefinition, 
    FactionDefinition, 
    WildlifeDefinition, 
    FloraDefinition
)

T = TypeVar('T', bound=BaseModel)

class DefinitionRegistry:
    """
    Loads and caches JSON simulation definition files (Assets).
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.resources: Dict[str, ResourceDefinition] = {}
        self.species: Dict[str, SpeciesDefinition] = {}
        self.factions: Dict[str, FactionDefinition] = {}
        self.wildlife: Dict[str, WildlifeDefinition] = {}
        self.flora: Dict[str, FloraDefinition] = {}

    def load_all(self):
        """Loads all JSON files from their respective subdirectories within data_dir/definitions/"""
        self.resources = self._load_category("resources", ResourceDefinition)
        self.species = self._load_category("species", SpeciesDefinition)
        self.factions = self._load_category("factions", FactionDefinition)
        self.wildlife = self._load_category("wildlife", WildlifeDefinition)
        self.flora = self._load_category("flora", FloraDefinition)
        print(f"[REGISTRY] Loaded {len(self.species)} species, {len(self.factions)} factions, {len(self.resources)} resources.")

    def _load_category(self, folder_name: str, model_type: Type[T]) -> Dict[str, T]:
        cache = {}
        folder_path = os.path.join(self.data_dir, "definitions", folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            return cache

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        obj = model_type(**data)
                        cache[obj.id] = obj
                except Exception as e:
                    print(f"[REGISTRY ERROR] Failed to load {filename}: {e}")
        return cache

    def save_definition(self, folder_name: str, obj: BaseModel):
        """Saves a single definition back to disk as JSON."""
        folder_path = os.path.join(self.data_dir, "definitions", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{obj.id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(obj.model_dump_json(indent=4))
