import sys
import os

print("--- DEBUG IMPORT CHECK ---")

try:
    print("Checking brain imports...")
    import brain.campaign_system as cs
    print("  campaign_system: OK")
except Exception as e:
    print(f"  campaign_system: FAILED - {e}")

try:
    print("Checking core imports...")
    sys.path.append(os.path.join(os.getcwd(), 'core'))
    import core.quest_manager as qm
    print("  quest_manager: OK")
    import core.item_generator as ig
    print("  item_generator: OK")
    import core.sensory_layer as sl
    print("  sensory_layer: OK")
    import combat.mechanics as cm
    print("  combat.mechanics: OK")
except Exception as e:
    print(f"  core/combat: FAILED - {e}")

print("--- FINISHED ---")
