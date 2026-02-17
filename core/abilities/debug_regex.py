
import re

pat = re.compile(r"Heal (\d+)?d?(\d+)? ?(HP)?", re.IGNORECASE)
text = "Heal 5 HP"
match = pat.search(text)

print(f"Text: '{text}'")
if match:
    print(f"MATCH: {match.groups()}")
else:
    print("NO MATCH")

# Test registry logic
patterns = []
patterns.append((pat, "HANDLER"))

def resolve(desc):
    print(f"Resolving: {desc}")
    for p, h in patterns:
        m = p.search(desc)
        if m:
            print(f"Found match with {h}")
            return
    print("No match found in registry loop")

resolve(text)
