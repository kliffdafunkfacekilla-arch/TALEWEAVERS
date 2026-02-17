class ChaosManager:
    """
    Manages the 'Chaos Clock' and narrative tension in the simulation.
    """
    def __init__(self):
        self.chaos_level = 0.1
        self.chaos_clock = 0
        self.max_chaos = 1.0

    def increment_chaos(self, amount=0.05):
        self.chaos_level = min(self.max_chaos, self.chaos_level + amount)
        self.chaos_clock += 1
        return self.chaos_level

    def reset_clock(self):
        self.chaos_clock = 0
