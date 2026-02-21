import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from brain.dependencies import get_db, DATA_DIR

router = APIRouter(prefix="/creator", tags=["character_creator"])

# --- Models ---
class FinalizeCharacterRequest(BaseModel):
    Name: str
    Species: str
    Level: int = 1
    Stats: Dict[str, int]
    Loadout: Dict[str, str]
    Triads: List[str]
    Backstory: str = ""
    School: str
    HP: int
    CMP: int
    Stamina: int
    Focus: int

# --- Helper Methods ---
def get_species_data() -> List[Dict[str, Any]]:
    species_dir = os.path.join(DATA_DIR, "Species")
    if not os.path.exists(species_dir):
        return []
    res = []
    for file in os.listdir(species_dir):
        if file.endswith(".json"):
            with open(os.path.join(species_dir, file), 'r', encoding='utf-8') as f:
                res.append(json.load(f))
    return res

def get_schools_data() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Schools_of_Power.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("schools", {})
    return {}

def get_items_data() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Item_Builder.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("item_system_v1", {}).get("categories", {})
    return {}

def get_triads_data() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Tactical_Triads.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("triads", {})
    return {}

def get_evolution_matrix() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Evolution_Matrix.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get("slots", {})
    return {}

def get_evolution_flavor() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Evolution_Kingdoms.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_backstory_scenarios() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "Backstory_Scenarios.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- Endpoints ---
@router.get("/data")
def get_creator_data():
    """Returns biological templates and magical schools for the VTT Wizard."""
    try:
        species = get_species_data()
        schools = get_schools_data()
        triads = get_triads_data()
        evolution = get_evolution_matrix()
        backstory = get_backstory_scenarios()
        flavor = get_evolution_flavor()
        items = get_items_data()
        return {
            "status": "success",
            "species": species,
            "schools": schools,
            "triads": triads,
            "evolution": evolution,
            "backstory": backstory,
            "evolution_flavor": flavor,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
def save_new_character(req: FinalizeCharacterRequest):
    """Compiles the wizard state into a rigid ECS-ready Save file."""
    try:
        saves_dir = os.path.join(DATA_DIR, "Saves")
        os.makedirs(saves_dir, exist_ok=True)
        
        file_name = f"{req.Name.replace(' ', '_')}.json"
        file_path = os.path.join(saves_dir, file_name)
        
        # Build strict Save State Format
        save_state = {
            "Name": req.Name,
            "Species": req.Species,
            "Level": req.Level,
            "Stats": req.Stats,
            "Loadout": req.Loadout,
            "Triads": req.Triads,
            "Backstory": req.Backstory,
            "School": req.School,
            "Inventory": [
                "Traveler's Cloak",
                "Waterskin",
                "Rations"
            ],
            "Gold": 50,
            "HP": req.HP,
            "CMP": req.CMP,
            "Stamina": req.Stamina,
            "Focus": req.Focus
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_state, f, indent=4)
            
        return {"status": "success", "message": f"{req.Name} generated successfully.", "file": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
