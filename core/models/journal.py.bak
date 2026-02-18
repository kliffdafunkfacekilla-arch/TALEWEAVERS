from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

@dataclass
class JournalEntry:
    timestamp: str
    archetype: str
    subject: str
    context: str
    reward: str
    chaos_twist: str
    narrative: str
    outcome: str = "Unresolved"
    metadata: Dict[str, Any] = field(default_factory=dict)

class Journal:
    def __init__(self):
        self.entries: List[JournalEntry] = []

    def log_event(self, archetype: str, subject: str, context: str, reward: str, chaos: str, narrative: str, goal: str = None) -> JournalEntry:
        entry = JournalEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            archetype=archetype,
            subject=subject,
            context=context,
            reward=reward,
            chaos_twist=chaos,
            narrative=narrative,
            metadata={"goal": goal} if goal else {}
        )
        self.entries.append(entry)
        return entry

    def resolve_last_event(self, outcome: str):
        if self.entries:
            self.entries[-1].outcome = outcome

    def get_summary(self) -> List[Dict[str, Any]]:
        return [vars(e) for e in self.entries]
