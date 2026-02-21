import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from brain.dependencies import db
from brain.routers import architect, tactical, narrative, character_creator, combat_api

# --- APP INITIALIZATION ---
app = FastAPI(
    title="SAYA: SAGA Brain API (v2.0)",
    description="Refactored modular API for the TALEWEAVERS simulation suite.",
    version="2.0.0"
)

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LIFESPAN MANAGEMENT ---
@app.on_event("startup")
async def startup_event():
    print("[SERVER] Taleweavers Brain v2.0 booting up...")
    db.load()
    print("[SERVER] World State Hydrated.")

# --- ROUTER REGISTRATION ---
app.include_router(architect.router)
app.include_router(tactical.router)
app.include_router(narrative.router)
app.include_router(character_creator.router)
app.include_router(combat_api.router)

# --- GLOBAL UTILITY ENDPOINTS ---
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "SAGA Brain",
        "version": "2.0.0",
        "modules": ["architect", "tactical", "narrative"]
    }

@app.post("/refresh")
def refresh_data():
    db.load()
    return {"status": "success", "message": "All database and RAG services reloaded."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
