import os

# T.A.L.E.W.E.A.V.E.R.S. Global Configuration for Python Suites
DATA_HUB = os.path.dirname(os.path.abspath(__file__))
TACTICAL_DATA = os.path.join(DATA_HUB, "tactical_data")
HISTORY_DATA = os.path.join(DATA_HUB, "history")

# Core Engine Files
LORE_JSON = os.path.join(DATA_HUB, "lore.json")
RULES_JSON = os.path.join(DATA_HUB, "rules.json")
TEMPLATES_JSON = os.path.join(DATA_HUB, "templates.json")
CALENDAR_JSON = os.path.join(DATA_HUB, "calendar.json")
MANUAL_MD = os.path.join(DATA_HUB, "manual.md")

# Tactical Data Files (BRQSE)
TTIS_JSON = os.path.join(TACTICAL_DATA, "ttis.json")
SCHOOLS_JSON = os.path.join(TACTICAL_DATA, "Schools_of_Power.json")
ENEMIES_JSON = os.path.join(TACTICAL_DATA, "Enemy_Builder.json")
ITEMS_JSON = os.path.join(TACTICAL_DATA, "Item_Builder.json")
CHAOS_JSON = os.path.join(TACTICAL_DATA, "chaos_core.json")

def get_session_path(session_id):
    return os.path.join(DATA_HUB, "sessions", f"{session_id}.json")
