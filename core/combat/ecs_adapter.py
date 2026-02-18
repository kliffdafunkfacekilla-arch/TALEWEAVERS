from core.ecs import Entity, Position, Vitals, Stats, Renderable, Inventory, Equipment, StatusEffects, FactionMember

class CombatEntity(Entity):
    """
    Adapter class that wraps an ECS Entity but exposes legacy properties
    (hp, x, y, stats) to maintain compatibility with the existing CombatEngine.
    """
    def __init__(self, name="Unnamed", data=None):
        super().__init__(name)
        
        # Initialize Core Components
        self.add_component(Position())
        self.add_component(Renderable())
        self.add_component(Stats())
        self.add_component(Vitals())
        self.add_component(Inventory())
        self.add_component(Equipment())
        self.add_component(StatusEffects())
        self.add_component(FactionMember())
        
        # Hydrate from JSON (if provided)
        if data:
            self.load_from_data(data)

    def load_from_data(self, data):
        # 1. Stats
        stats = data.get("Stats", {})
        self.get_component(Stats).attrs = stats
        
        # 2. Vitals (Calculate from Stats)
        vitals = self.get_component(Vitals)
        s = self.get_component(Stats)
        
        # Formulas (Matches mechanics.py)
        vitals.max_hp = 10 + s.get("Might") + s.get("Reflexes") + s.get("Vitality")
        vitals.max_sp = s.get("Endurance") + s.get("Finesse") + s.get("Fortitude")
        vitals.max_fp = s.get("Knowledge") + s.get("Charm") + s.get("Intuition")
        
        # Current Values (default to max unless specified)
        vitals.hp = data.get("HP", vitals.max_hp)
        vitals.sp = data.get("SP", vitals.max_sp)
        vitals.fp = data.get("FP", vitals.max_fp)
        
        # 3. Renderable
        rend = self.get_component(Renderable)
        rend.icon = data.get("Icon", "token.png")
        rend.color = data.get("Color", "#ffffff")
        
        # 4. Inventory
        inv = self.get_component(Inventory)
        inv.items = data.get("Inventory", [])

    # --- LEGACY PROPERTY ADAPTERS ---

    @property
    def x(self): return self.get_component(Position).x
    @x.setter
    def x(self, val): self.get_component(Position).x = val

    @property
    def y(self): return self.get_component(Position).y
    @y.setter
    def y(self, val): self.get_component(Position).y = val

    @property
    def hp(self): return self.get_component(Vitals).hp
    @hp.setter
    def hp(self, val): self.get_component(Vitals).hp = val

    @property
    def max_hp(self): return self.get_component(Vitals).max_hp
    @max_hp.setter
    def max_hp(self, val): self.get_component(Vitals).max_hp = val

    @property
    def sp(self): return self.get_component(Vitals).sp
    @sp.setter
    def sp(self, val): self.get_component(Vitals).sp = val

    @property
    def max_sp(self): return self.get_component(Vitals).max_sp
    @max_sp.setter
    def max_sp(self, val): self.get_component(Vitals).max_sp = val

    @property
    def fp(self): return self.get_component(Vitals).fp
    @fp.setter
    def fp(self, val): self.get_component(Vitals).fp = val
    
    @property
    def max_fp(self): return self.get_component(Vitals).max_fp
    @max_fp.setter
    def max_fp(self, val): self.get_component(Vitals).max_fp = val
    
    @property
    def stats(self): return self.get_component(Stats).attrs
    @stats.setter
    def stats(self, val): self.get_component(Stats).attrs = val

    def get_stat(self, name):
        return self.get_component(Stats).get(name)

    # Re-implement methods used by CombatEngine using Components
    def take_damage(self, amount):
        v = self.get_component(Vitals)
        actual = min(amount, v.hp)
        v.hp -= actual
        return actual
