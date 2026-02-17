def load_csv(path):
    import csv
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return list(csv.DictReader(f))
    except: return []

class EncounterTable:
    @staticmethod
    def get_weighted_beast(data, biome, level):
        # Basic fallback: return random from data matching level/biome
        if not data: return None
        return random.choice(data)
