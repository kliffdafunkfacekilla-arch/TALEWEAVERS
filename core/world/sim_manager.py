import math
import random
from core.ecs import world_ecs, Logistics

class SimulationManager:
    """
    Manages the 4-Tier Simulation Ticking Logic with Focal Point (LOD) abstraction.
    Detail Level transitions: High (Player) -> Mid (Local) -> Abstract (Regional Manager) -> Macro (Global)
    """
    
    # Simulation Radii in Map Units
    DEPTH_TACTICAL = 50   # Full entity-level simulation
    DEPTH_LOCAL    = 250  # Narrative/Trade simulation
    DEPTH_REGIONAL = 750  # Statistical influence simulation
    
    def __init__(self, state):
        self.state = state
        self.narrative_hours = 0
        
    def advance_time(self, hours: int, player_pos: tuple = (500, 500)):
        """Passes narrative time and triggers LOD-based simulation ticks."""
        self.narrative_hours += hours
        
        # 0. Catch-up Logic for Nearby Nodes
        self._check_for_catchups(player_pos)

        # 1. Player Level: Always High Detail (Hourly)
        self.tick_player_sim(hours, player_pos)
        
        # 2. Local Level: Daily
        if self.narrative_hours % 24 == 0:
            self.tick_local_sim(player_pos)
            
        # 3. Regional Level: Weekly
        if self.narrative_hours % 168 == 0:
            self.tick_regional_sim(player_pos)
            
        # 4. Global Level: Monthly (Always Macro-level)
        if self.narrative_hours % 672 == 0:
            self.tick_global_sim()
            
        # 5. ECS LOGISTICS BATCH SIM
        self.batch_logistic_tick(hours)
            
    def _get_dist(self, pos1, pos2):
        return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

    def batch_logistic_tick(self, delta_hours: int):
        """
        Iterates over all ECS entities with Logistics components and 
        processes resource depletion, production, and population shifts.
        """
        print(f"[SIM-BATCH] Processing Logistics for {delta_hours} hours...")
        
        for entity in world_ecs.get_entities_with(Logistics):
            log = entity.get_component(Logistics)
            
            # Resource Depletion (Consumption)
            for res, rate in log.needs.items():
                if res in log.resources:
                    consumption = rate * log.population * delta_hours
                    log.resources[res] -= consumption
                    
                    # Population Famine Check
                    if log.resources[res] < 0:
                        log.resources[res] = 0
                        # Statistically kill off some pop due to famine
                        famine_deaths = int(log.population * 0.05 * (delta_hours / 24))
                        log.population = max(0, log.population - famine_deaths)
                        print(f"  -> FAMINE alert in {entity.name}: {famine_deaths} deaths.")

            # Production (Simplified)
            # If they have food, they grow.
            if log.resources.get("Food", 0) > log.population:
                growth = int(log.population * 0.001 * delta_hours)
                log.population += growth

            log.last_tick = self.narrative_hours

    def _check_for_catchups(self, player_pos):
        """Finds nodes that just entered the simulation zone and fast-forwards them."""
        for node in self.state.get('nodes', []):
            dist = self._get_dist(player_pos, (node.get('x', 0), node.get('y', 0)))
            if dist < self.DEPTH_LOCAL:
                last_tick = node.get('last_tick', 0)
                if last_tick < self.narrative_hours:
                    self._catch_up_node(node, self.narrative_hours)

    def _catch_up_node(self, node, current_hours):
        """Statistically simulates missed time for a node."""
        last_t = node.get('last_tick', 0)
        delta = current_hours - last_t
        days_missed = delta // 24
        
        if days_missed > 0:
            node['stats'] = node.get('stats', {'wealth': 100, 'pop': 50})
            node['stats']['wealth'] += days_missed * 1.5
            node['stats']['pop'] *= (1.001 ** days_missed) 
            
            node['last_tick'] = current_hours
            print(f"[SIM-LOD] Caught up {node.get('name')} over {days_missed} missed days.")

    def tick_player_sim(self, hours, player_pos):
        active_nodes = [n for n in self.state.get('nodes', []) 
                       if self._get_dist(player_pos, (n.get('x',0), n.get('y',0))) < self.DEPTH_TACTICAL]
        for node in active_nodes:
            node['last_tick'] = self.narrative_hours

    def tick_local_sim(self, player_pos):
        local_nodes = [n for n in self.state.get('nodes', []) 
                      if self._get_dist(player_pos, (n.get('x',0), n.get('y',0))) < self.DEPTH_LOCAL]
        for node in local_nodes:
            node['last_tick'] = self.narrative_hours
            node['stats'] = node.get('stats', {'wealth': 100, 'pop': 50})
            node['stats']['wealth'] += 10

    def tick_regional_sim(self, player_pos):
        if 'meta' in self.state:
            self.state['meta']['global_wealth'] += 10 
            
        factions = self.state.get('factions', [])
        nodes = self.state.get('nodes', [])
        
        for faction in factions:
            faction['power'] = faction.get('power', 0) + random.randint(1, 5)
            if faction['power'] > 50:
                neutral_nodes = [n for n in nodes if n.get('faction_id') is None]
                if neutral_nodes:
                    target = random.choice(neutral_nodes)
                    target['faction_id'] = faction['id']
                    target['faction_name'] = faction['name']
                    # Link to ECS also?
                    faction['power'] -= 30

    def tick_global_sim(self):
        if 'meta' in self.state:
            self.state['meta']['epoch'] += 1
            self.state['meta']['global_pop'] *= 1.01

    def get_time_string(self):
        days = self.narrative_hours // 24
        remaining_hours = self.narrative_hours % 24
        return f"Day {days}, Hour {remaining_hours}"
