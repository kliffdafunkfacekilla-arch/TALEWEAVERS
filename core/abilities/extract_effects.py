
from data_loader import DataLoader
import os

def extract():
    dl = DataLoader()
    effects = dl.get_all_effects()
    
    # Categorize effects
    # We'll try to group them by keywords to make the list more actionable
    categories = {
        "PASSIVE_STAT": [],
        "PASSIVE_SKILL": [],
        "ON_ATTACK": [],
        "ON_HIT": [],
        "ON_DEFEND": [],
        "ACTIVE": [],
        "OTHER": []
    }
    
    for e in effects:
        lower_e = e.lower()
        if "passive" in lower_e:
            if "might" in lower_e or "reflex" in lower_e or "resilience" in lower_e or "speed" in lower_e:
                categories["PASSIVE_STAT"].append(e)
            else:
                categories["PASSIVE_SKILL"].append(e)
        elif "attack" in lower_e:
            categories["ON_ATTACK"].append(e)
        elif "hit" in lower_e or "damage" in lower_e:
            categories["ON_HIT"].append(e)
        elif "defend" in lower_e or "dodge" in lower_e:
            categories["ON_DEFEND"].append(e)
        elif "action" in lower_e or "cast" in lower_e:
            categories["ACTIVE"].append(e)
        else:
            categories["OTHER"].append(e)

    # Write to MD
    out_path = os.path.join(os.path.dirname(__file__), "EFFECTS_TODO.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Effects to Implement\n\n")
        
        for cat, items in categories.items():
            f.write(f"## {cat} ({len(items)})\n")
            for item in items:
                f.write(f"- [ ] {item}\n")
            f.write("\n")
            
    print(f"Extracted {len(effects)} effects to {out_path}")

if __name__ == "__main__":
    extract()
