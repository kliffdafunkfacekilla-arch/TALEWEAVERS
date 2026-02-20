import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize Database and Logic
from brain.dependencies import db
db.load()

# Import Routers
from brain.routers import architect, tactical, narrative

print("[BOOT] Taleweavers Brain initializing...")

# --- APP SETUP ---
app = FastAPI(title="SAYA: SAGA Brain API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUDE ROUTERS ---
app.include_router(architect.router)
app.include_router(tactical.router)
app.include_router(narrative.router)

@app.get("/")
def health_check():
    return {"status": "online", "routers": ["architect", "tactical", "narrative"], "lore_count": len(db.lore)}

@app.post("/refresh")
def refresh_data():
    db.load()
    return {"status": "refreshed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
