from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class ResourceDefinition(BaseModel):
    id: str
    name: str
    category: str = Field(..., description="e.g., 'food', 'material', 'wealth', 'luxury'")
    rarity: float = Field(0.5, ge=0.0, le=1.0)
    spawn_biomes: List[str] = []
    is_finite: bool = False
    bonuses: Dict[str, float] = Field(default_factory=dict, description="e.g., {'temp_tolerance': 5.0, 'speed': 1.1}")

class SpeciesTaskWeights(BaseModel):
    farm: float = 1.0
    mine: float = 1.0
    hunt: float = 1.0
    trade: float = 1.0
    build: float = 1.0

class SpeciesDefinition(BaseModel):
    id: str
    name: str
    growth_rate: float = 0.05
    strength: float = 10.0
    speed: float = 10.0
    water_requirement: float = 0.5 # 0.0 (desert) to 1.0 (aquatic)
    min_temp_tolerance: float = -10.0
    max_temp_tolerance: float = 40.0
    favored_biomes: List[str] = []
    hated_biomes: List[str] = []
    task_weights: SpeciesTaskWeights = Field(default_factory=SpeciesTaskWeights)
    resource_needs: Dict[str, float] = Field(default_factory=dict) # E.g., {"food": 1.0, "water": 1.0}

class FactionDefinition(BaseModel):
    id: str
    name: str
    primary_species_id: str
    aggression: float = Field(0.5, ge=0.0, le=1.0)
    trade_focus: float = Field(0.5, ge=0.0, le=1.0)
    expansion_drive: float = Field(0.5, ge=0.0, le=1.0)

class WildlifeDefinition(BaseModel):
    id: str
    name: str
    hostile: bool = False
    tamable: bool = False
    farmable: bool = False
    growth_rate: float = 0.1
    water_requirement: float = 0.5
    min_temp_tolerance: float = -20.0
    max_temp_tolerance: float = 50.0
    spawn_biomes: List[str] = []
    resource_yields: Dict[str, int] = Field(default_factory=dict)

class FloraDefinition(BaseModel):
    id: str
    name: str
    toxic: bool = False
    farmable: bool = True
    growth_rate: float = 0.2
    water_requirement: float = 0.8
    min_temp_tolerance: float = 0.0
    max_temp_tolerance: float = 40.0
    spawn_biomes: List[str] = []
    resource_yields: Dict[str, int] = Field(default_factory=dict)
