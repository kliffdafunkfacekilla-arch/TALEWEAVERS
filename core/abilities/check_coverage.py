
import os
import re
import sys

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from abilities.effects_registry import registry

class MockContext(dict):
    def get(self, key, default=None):
        # Return a dummy object for 'attacker'/'target' so attribute access doesn't fail
        if key in ['attacker', 'target']:
            return MockEntity()
        return super().get(key, default)

class MockEntity:
    def __init__(self):
        self.name = "Mock"
        self.hp = 10
        self.max_hp = 10
        self.sp = 10
        self.fp = 10
        self.cmp = 10
        self.x = 0
        self.y = 0

def check():
    path = os.path.join(os.path.dirname(__file__), "EFFECTS_TODO.md")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    total = 0
    handled = 0
    unhandled = []
    
    ctx = MockContext()
    ctx['log'] = []
    
    current_cat = "Unknown"
    
    for line in lines:
        line = line.strip()
        if line.startswith("##"):
            current_cat = line.replace("#", "").strip()
            continue
            
        if not line.startswith("- [ ]"): continue
        
        # Extract description part (after "->")
        # Format: - [ ] Source: Name -> Description
        parts = line.split(" -> ")
        if len(parts) < 2: continue
        
        desc = parts[1]
        total += 1
        
        try:
            if registry.resolve(desc, ctx):
                handled += 1
            else:
                unhandled.append(f"[{current_cat}] {desc}")
        except:
             # If it crashes, it's unhandled/buggy
             unhandled.append(f"[{current_cat}] (CRASH) {desc}")

    print(f"Total Effects: {total}")
    print(f"Handled: {handled}")
    print(f"Unhandled: {len(unhandled)}")
    print("\n--- Top Unhandled Examples ---")
    for u in unhandled[:20]:
        print(u)
        
    # Write full unhandled list to file
    out_path = os.path.join(os.path.dirname(__file__), "unhandled_report.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for u in unhandled:
            f.write(u + "\n")
    print(f"\nFull list written to {out_path}")

if __name__ == "__main__":
    check()
