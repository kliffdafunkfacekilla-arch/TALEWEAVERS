class Inventory:
    """
    Standardized Inventory management for Combatants.
    """
    def __init__(self, owner=None):
        self.owner = owner
        self.items = []
        self.capacity = 20

    def add_item(self, item):
        if len(self.items) < self.capacity:
            self.items.append(item)
            return True
        return False

    def remove_item(self, item_id):
        self.items = [i for i in self.items if i.get('id') != item_id]
