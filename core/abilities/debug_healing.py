
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from abilities.effects_registry import registry

class MockUser:
    def __init__(self):
        self.name = "Tester"
        self.hp = 10
        self.max_hp = 20

def test_manual_resolve():
    user = MockUser()
    ctx = {
        "attacker": user,
        "target": user,
        "log": []
    }
    
    desc = "Heal 5 HP"
    print(f"Resolving: '{desc}'")
    res = registry.resolve(desc, ctx)
    
    print(f"Handled: {res}")
    print(f"User HP: {user.hp}")
    print(f"Log: {ctx['log']}")

if __name__ == "__main__":
    test_manual_resolve()
