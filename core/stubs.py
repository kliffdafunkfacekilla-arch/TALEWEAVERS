import random

class Dice:
    @staticmethod
    def roll(expr="1d20"):
        # Simple parser for d20 rolls
        try:
            num, sides = map(int, expr.lower().split('d'))
            rolls = [random.randint(1, sides) for _ in range(num)]
            return sum(rolls), rolls, 0
        except:
            return random.randint(1, 20), [0], 0

class StatusManager:
    def __init__(self, owner):
        self.owner = owner
        self.conditions = set()
        self.timed_effects = []

    def add_condition(self, condition, duration=1):
        self.conditions.add(condition)

    def remove_condition(self, condition):
        if condition in self.conditions:
            self.conditions.remove(condition)

    def has(self, condition):
        return condition in self.conditions

    def tick(self):
        return []

class Conditions:
    PRONE = "Prone"
    GRAPPLED = "Grappled"
    BLINDED = "Blinded"
    RESTRAINED = "Restrained"
    STUNNED = "Stunned"
    PARALYZED = "Paralyzed"
    POISONED = "Poisoned"
    FRIGHTENED = "Frightened"
    CHARMED = "Charmed"
    DEAFENED = "Deafened"
    INVISIBLE = "Invisible"
    CONFUSED = "Confused"
    BERSERK = "Berserk"
    STAGGERED = "Staggered"
    BURNING = "Burning"
    BLEEDING = "Bleeding"
    FROZEN = "Frozen"
    SANCTUARY = "Sanctuary"

class Stats:
    MIGHT = "Might"
    REFLEXES = "Reflexes"
    ENDURANCE = "Endurance"
    VITALITY = "Vitality"
    FORTITUDE = "Fortitude"
    KNOWLEDGE = "Knowledge"
    LOGIC = "Logic"
    AWARENESS = "Awareness"
    INTUITION = "Intuition"
    CHARM = "Charm"
    WILLPOWER = "Willpower"
    FINESSE = "Finesse"

class DataLoader:
    def get_item_data(self, name):
        return {"Name": name}
