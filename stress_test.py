import requests
import time
import sys

API_URL = "http://localhost:8000"

def run_stress_test():
    print("--- 🚀 TALEWEAVERS HEADLESS API STRESS TEST 🚀 ---")
    
    # 1. Load the combat encounter
    print("[1] Initializing Battle Lab...")
    try:
        resp = requests.post(f"{API_URL}/combat/load", json={"character_name": "Burt"})
        resp.raise_for_status()
        data = resp.json()
        print(f"✅ Board initialized. Player deployed at: {data['player_data'].get('pos')}")
    except Exception as e:
        print(f"❌ Failed to load combat encounter: {e}")
        sys.exit(1)
        
    # 2. Simulate 50 rounds of combat (Player does nothing, AI takes all actions)
    rounds_to_simulate = 50
    print(f"\n[2] Simulating {rounds_to_simulate} rounds of AI combat...")
    
    start_time = time.time()
    
    try:
        for i in range(1, rounds_to_simulate + 1):
            if i % 10 == 0:
                print(f"  -> Simulating Round {i} / {rounds_to_simulate}...")
                
            resp = requests.post(f"{API_URL}/combat/end_turn")
            resp.raise_for_status()
            
            data = resp.json()
            
            # Check if player died or all enemies died (though player does nothing so they'll die)
            player_hp = data['state']['player_data']['hp']
            if player_hp <= 0:
                print(f"💀 PLAYER KILLED AT ROUND {i}!")
                break
                
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE DURING ROUND {i}: {e}")
        if resp:
            print(f"Response: {resp.text}")
        sys.exit(1)
        
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ STRESS TEST COMPLETE!")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Rounds Processed: {i}")
    print("The SAGA engine successfully handled heavy AI pathfinding and dynamic ability usage without crashing.")

if __name__ == "__main__":
    run_stress_test()
