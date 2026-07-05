"""PawPal+ system classes: Owner, Pet, Task, Scheduler.

Skeleton only — mirrors diagrams/uml_draft.mmd. Scheduling logic is not implemented yet.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    preferred_time: str | None = None
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True


@dataclass
class Pet:
    id: str
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        return self.tasks


@dataclass
class Owner:
    id: str
    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        return self.pets


@dataclass
class ScheduleEntry:
    task: Task
    start_time: str
    end_time: str
    reason: str


@dataclass
class Schedule:
    date: str
    entries: list[ScheduleEntry] = field(default_factory=list)

    def add_entry(self, entry: ScheduleEntry) -> None:
        self.entries.append(entry)

    def get_entries(self) -> list[ScheduleEntry]:
        return self.entries


class Scheduler:
    """Builds a Schedule from a list of Tasks given constraints. Logic TBD."""

    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def build_schedule(self, tasks: list[Task], constraints: dict) -> Schedule:
        raise NotImplementedError

    def explain_schedule(self, schedule: Schedule) -> str:
        raise NotImplementedError

    def _prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        raise NotImplementedError

    def _resolve_conflicts(self, tasks: list[Task]) -> list[Task]:
        raise NotImplementedError
