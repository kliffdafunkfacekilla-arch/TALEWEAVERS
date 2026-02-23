import json
import uuid
import os
from typing import List, Dict, Any, Optional

class QuestObjective:
    def __init__(self, description: str, slug: str, target_count: int = 1, current_count: int = 0, is_complete: bool = False):
        self.description = description
        self.slug = slug
        self.target_count = target_count
        self.current_count = current_count
        self.is_complete = is_complete

    def update(self, delta: int = 1):
        self.current_count += delta
        if self.current_count >= self.target_count:
            self.is_complete = True
        return self.is_complete

    def to_dict(self):
        return vars(self)

class Quest:
    def __init__(self, title: str, description: str, objectives: List[Dict[str, Any]], rewards: Dict[str, Any] = None):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.status = "ACTIVE" # ACTIVE, COMPLETED, FAILED
        self.objectives = [QuestObjective(**obj) for obj in objectives]
        self.rewards = rewards or {"gold": 0, "xp": 0, "items": []}
        self.narrative_hook = "" # Specific context for the Oracle

    def check_completion(self):
        if all(obj.is_complete for obj in self.objectives):
            self.status = "COMPLETED"
            return True
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "objectives": [obj.to_dict() for obj in self.objectives],
            "rewards": self.rewards,
            "narrative_hook": self.narrative_hook
        }

class QuestManager:
    def __init__(self, save_path: Optional[str] = None, persistence_layer=None):
        self.quests: List[Quest] = []
        self.save_path = save_path
        self.db = persistence_layer

    def add_quest(self, quest_data: Dict[str, Any]):
        new_quest = Quest(
            title=quest_data["title"],
            description=quest_data["description"],
            objectives=quest_data["objectives"],
            rewards=quest_data.get("rewards")
        )
        new_quest.narrative_hook = quest_data.get("narrative_hook", "")
        self.quests.append(new_quest)
        return new_quest.id

    def update_objective(self, slug: str, delta: int = 1):
        updates = []
        for quest in self.quests:
            if quest.status != "ACTIVE": continue
            for obj in quest.objectives:
                if obj.slug == slug:
                    was_complete = obj.is_complete
                    obj.update(delta)
                    if not was_complete and obj.is_complete:
                        updates.append(f"Objective Complete: {obj.description}")
                        if quest.check_completion():
                            updates.append(f"QUEST COMPLETE: {quest.title}")
        return updates

    def get_active_quests(self):
        return [q.to_dict() for q in self.quests if q.status == "ACTIVE"]

    def save(self, path=None):
        # 1. Save to SQLite if DB available
        if self.db:
            for q in self.quests:
                self.db.save_quest(q.id, q.title, q.description, q.status, q.to_dict())
            print(f"[QUESTS] Synced {len(self.quests)} quests to SQLite.")

        # 2. Fallback/Dual save to JSON
        target = path or self.save_path
        if not target: return
        with open(target, 'w') as f:
            json.dump([q.to_dict() for q in self.quests], f, indent=4)

    def load(self, path=None):
        # 1. Try loading from SQLite first
        if self.db:
            db_quests = self.db.load_all_quests()
            if db_quests:
                self.quests = []
                for q_data in db_quests:
                    q = self._reconstruct_quest(q_data["data"])
                    q.status = q_data["status"]
                    self.quests.append(q)
                print(f"[QUESTS] Loaded {len(self.quests)} quests from SQLite.")
                return

        # 2. Fallback to JSON
        target = path or self.save_path
        if not target or not os.path.exists(target): return
        with open(target, 'r') as f:
            data = json.load(f)
            self.quests = []
            for q_data in data:
                self.quests.append(self._reconstruct_quest(q_data))

    def _reconstruct_quest(self, q_data: Dict[str, Any]) -> Quest:
        q = Quest(q_data["title"], q_data["description"], [])
        q.id = q_data["id"]
        q.status = q_data["status"]
        q.objectives = [QuestObjective(**obj) for obj in q_data["objectives"]]
        q.rewards = q_data["rewards"]
        q.narrative_hook = q_data.get("narrative_hook", "")
        return q
