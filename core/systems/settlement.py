from core.ecs import ECSRegistry, Demographics, Economy, Infrastructure, Logistics
from core.definition_registry import DefinitionRegistry

class SettlementSystem:
    """
    Processes the demographic growth, economic trading, and unrest 
    of entities holding Demographic/Economy components over time.
    Provides the deep 'Local' layer simulation data for the 4-layer hierarchy.
    """
    def __init__(self, registry: ECSRegistry, definitions: DefinitionRegistry):
        self.registry = registry
        self.definitions = definitions

    def process_tick(self):
        """Advances the simulation by one abstract tick (e.g., a month)."""
        
        # 1. Process Population Growth and Logistics (Species Asset Driven)
        for entity in self.registry.get_entities_with(Demographics, Logistics):
            demo = entity.get_component(Demographics)
            logistics = entity.get_component(Logistics)
            
            # Identify active species ruleset
            species_id = entity.properties.get("species_id", "human") # Fallback
            species_def = self.definitions.species.get(species_id)
            
            if not species_def:
                continue # Skip if no species definition exists
                
            # Base growth from Species Definition
            growth_rate = species_def.growth_rate
            
            # Simple logistic growth model
            if demo.pop_total < demo.pop_capacity:
                growth = int(demo.pop_total * growth_rate)
                
                # Check food/water constraints based on species needs
                water_req = species_def.water_requirement * demo.pop_total
                food_consumed = demo.pop_total * species_def.resource_needs.get("food", 1.0)
                
                food = logistics.resources.get("food", 0)
                
                if food >= food_consumed:
                    demo.pop_total += growth
                    logistics.resources["food"] = max(0, int(food - food_consumed))
                    demo.social_unrest = max(0.0, demo.social_unrest - 0.01) # Happy
                else:
                    # Starvation
                    starved = int((food_consumed - food) / species_def.resource_needs.get("food", 1.0))
                    demo.pop_total = max(0, demo.pop_total - starved)
                    logistics.resources["food"] = 0
                    demo.social_unrest = min(1.0, demo.social_unrest + 0.1) # Unhappy
                    
            logistics.population = demo.pop_total # Sync legacy component

        # 2. Process Economy and Taxation (Faction/Culture Driven)
        for entity in self.registry.get_entities_with(Demographics, Economy):
            demo = entity.get_component(Demographics)
            econ = entity.get_component(Economy)
            
            # Generate local wealth based on population and taxation
            tax_revenue = demo.pop_total * econ.tax_rate
            
            # Unrest hurts economy
            efficiency = 1.0 - demo.social_unrest
            tax_revenue *= efficiency
            
            # Fetch species to determine task weights
            species_id = entity.properties.get("species_id", "human")
            species_def = self.definitions.species.get(species_id)
            work_efficiency = efficiency
            if species_def:
                # E.g. If the primary export requires farming, use farm weight
                work_efficiency *= species_def.task_weights.farm

            econ.wealth += int(tax_revenue)
            
            # Simple production based on primary export
            logistics = entity.get_component(Logistics)
            if logistics:
                production_amount = int((demo.pop_total * 0.1) * work_efficiency)
                current = logistics.resources.get(econ.primary_export, 0)
                logistics.resources[econ.primary_export] = current + production_amount

        # 3. Process Trade between Settlements (Simple Proximity/Global Model)
        # Note: In a full GIS model, this would use the network graph.
        settlements = list(self.registry.get_entities_with(Economy, Logistics))
        for seller in settlements:
            s_econ = seller.get_component(Economy)
            s_log = seller.get_component(Logistics)
            s_demo = seller.get_component(Demographics)
            s_infra = seller.get_component(Infrastructure)
            
            faction_id = seller.properties.get("faction_id", "neutral")
            faction_def = self.definitions.factions.get(faction_id)
            expansion_drive = faction_def.expansion_drive if faction_def else 0.5
            
            # Crime: High unrest leads to Banditry (Steals wealth/resources)
            if s_demo and s_demo.social_unrest > 0.75:
                # Bandits siphon wealth off trade routes
                if s_econ.wealth > 50:
                    stolen = int(s_econ.wealth * 0.15)
                    s_econ.wealth -= stolen
                    
            export_good = s_econ.primary_export
            export_qty = s_log.resources.get(export_good, 0)
            
            if export_qty <= 0: continue
            
            for buyer in settlements:
                if buyer.id == seller.id: continue
                b_econ = buyer.get_component(Economy)
                b_log = buyer.get_component(Logistics)
                
                # If buyer wants what seller has, and buyer has wealth
                import_good = b_econ.primary_import
                if import_good == export_good:
                    price = s_econ.market_prices.get(export_good, 1.0)
                    
                    # Compute max amount buyer can afford
                    max_affordable = int(b_econ.wealth / price)
                    
                    # Try to buy up to 50 units, or whatever they can afford
                    qty_to_buy = min(50, export_qty, max_affordable)
                    
                    if qty_to_buy > 0:
                        # Transaction
                        cost = int(qty_to_buy * price)
                        b_econ.wealth -= cost
                        s_econ.wealth += cost
                        
                        s_log.resources[export_good] -= qty_to_buy
                        current_import = b_log.resources.get(import_good, 0)
                        b_log.resources[import_good] = current_import + qty_to_buy
                        
                        export_qty -= qty_to_buy
                        
                        # Infrastructure: High expansion + active trade builds roads
                        if expansion_drive > 0.6:
                            if s_infra:
                                s_infra.trade_level = min(10.0, s_infra.trade_level + 0.05)
                            b_infra = buyer.get_component(Infrastructure)
                            if b_infra:
                                b_infra.trade_level = min(10.0, b_infra.trade_level + 0.05)
                    
                    if export_qty <= 0: break
