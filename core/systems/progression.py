class ProgressionEngine:
    """
    Handles character advancement, trait unlocking, and stat scaling.
    """
    
    def check_unlocks(self, combatant):
        """
        Analyzes a combatant's stats/level and returns a list of newly unlocked traits.
        """
        new_traits = []
        stats = combatant.stats if hasattr(combatant, 'stats') else {}
        current_traits = combatant.data.get("Traits", [])
        
        # Example: Unlock 'Resilient' if Vitality > 15
        if stats.get("Vitality", 10) >= 15 and "Resilient" not in current_traits:
            new_traits.append("Resilient")
            
        # Example: Unlock 'Weapon Master' if Finesse > 15
        if stats.get("Finesse", 10) >= 15 and "Weapon Master" not in current_traits:
            new_traits.append("Weapon Master")
            
        return new_traits

    def award_xp(self, combatant, amount):
        """Standardizes XP gain logic."""
        if not hasattr(combatant, 'xp'):
            combatant.xp = 0
        combatant.xp += amount
        return combatant.xp
