"""PawPal+ system classes: Owner, Pet, Task, Scheduler.

Skeleton only — mirrors diagrams/uml_draft.mmd. Scheduling logic is not implemented yet.
"""

from dataclasses import dataclass, field


def _time_to_minutes(time_str: str) -> int:
    """Convert an "HH:MM" string into minutes since midnight."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight into an "HH:MM" string."""
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# VALID_PRIORITIES = {"low", "medium", "high"}  # priority disabled for now, re-enable later
VALID_FREQUENCIES = {"once", "daily", "weekly"}


@dataclass
class Task:
    id: str
    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    pet_id: str  # back-reference so a flat list of tasks can be traced to its pet
    description: str = ""
    frequency: str = "once"  # "once" | "daily" | "weekly"
    preferred_time: str | None = None
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate frequency and duration after the dataclass fields are set."""
        # Priority validation disabled for now — re-enable when priority-based scheduling returns.
        # if self.priority not in VALID_PRIORITIES:
        #     raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got {self.priority!r}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes!r}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not yet completed."""
        self.completed = False

    def is_recurring(self) -> bool:
        """Return True if this task repeats (frequency other than "once")."""
        return self.frequency != "once"


@dataclass
class Pet:
    id: str
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet, enforcing a matching pet_id and a unique task id."""
        # Fix: enforce that a task's pet_id always matches the pet it's added to
        if task.pet_id != self.id:
            raise ValueError(
                f"task.pet_id ({task.pet_id!r}) does not match pet.id ({self.id!r})"
            )
        if any(existing.id == task.id for existing in self.tasks):
            raise ValueError(f"task with id {task.id!r} already exists for pet {self.id!r}")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet, if present."""
        self.tasks = [task for task in self.tasks if task.id != task_id]

    def get_task(self, task_id: str) -> Task | None:
        """Return the task with the given id, or None if not found."""
        return next((task for task in self.tasks if task.id == task_id), None)

    def get_tasks(self) -> list[Task]:
        """Return all tasks belonging to this pet."""
        return self.tasks

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [task for task in self.tasks if not task.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return this pet's tasks that are already completed."""
        return [task for task in self.tasks if task.completed]

    def total_duration_minutes(self) -> int:
        """Return the combined duration, in minutes, of all this pet's tasks."""
        return sum(task.duration_minutes for task in self.tasks)


@dataclass
class Owner:
    id: str
    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, enforcing a unique pet id."""
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError(f"pet with id {pet.id!r} already exists for owner {self.id!r}")
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet with the given id from this owner, if present."""
        self.pets = [pet for pet in self.pets if pet.id != pet_id]

    def get_pet(self, pet_id: str) -> Pet | None:
        """Return the pet with the given id, or None if not found."""
        return next((pet for pet in self.pets if pet.id == pet_id), None)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of tasks across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_pending_tasks(self) -> list[Task]:
        """Return this owner's tasks, across all pets, that are not yet completed."""
        return [task for task in self.get_all_tasks() if not task.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return this owner's tasks, across all pets, that are already completed."""
        return [task for task in self.get_all_tasks() if task.completed]


@dataclass
class ScheduleEntry:
    task: Task
    start_time: str
    end_time: str
    reason: str

    def duration_minutes(self) -> int:
        """Return how many minutes this entry occupies."""
        return _time_to_minutes(self.end_time) - _time_to_minutes(self.start_time)

    def overlaps(self, other: "ScheduleEntry") -> bool:
        """Return True if this entry's time range overlaps another entry's."""
        start, end = _time_to_minutes(self.start_time), _time_to_minutes(self.end_time)
        other_start, other_end = _time_to_minutes(other.start_time), _time_to_minutes(other.end_time)
        return start < other_end and other_start < end

    def __str__(self) -> str:
        """Return a human-readable one-line summary of this entry."""
        return f"{self.start_time}-{self.end_time}  {self.task.title} - {self.reason}"


@dataclass
class Schedule:
    date: str
    entries: list[ScheduleEntry] = field(default_factory=list)

    def add_entry(self, entry: ScheduleEntry) -> None:
        """Add an entry to this schedule."""
        self.entries.append(entry)

    def get_entries(self) -> list[ScheduleEntry]:
        """Return this schedule's entries sorted chronologically by start time."""
        return sorted(self.entries, key=lambda entry: _time_to_minutes(entry.start_time))

    def total_scheduled_minutes(self) -> int:
        """Return the combined duration, in minutes, of all entries in this schedule."""
        return sum(entry.duration_minutes() for entry in self.entries)

    def find_entry_for_task(self, task_id: str) -> ScheduleEntry | None:
        """Return the entry for the given task id, or None if not scheduled."""
        return next((entry for entry in self.entries if entry.task.id == task_id), None)


# PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}  # priority disabled for now, re-enable later


class Scheduler:
    """Builds a Schedule from a list of Tasks given constraints.

    Constraints supported:
      - "date": str, stamped onto the resulting Schedule
      - "start_time": "HH:MM", when the day's schedule begins (default "08:00")
      - "available_minutes": int | None, total time budget for the day (default None = unlimited)
    """

    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def build_schedule(self, tasks: list[Task], constraints: dict) -> Schedule:
        """Build a Schedule for the given tasks, respecting the given constraints."""
        self.tasks = list(tasks)
        pending = [task for task in self.tasks if not task.completed]
        resolved = self._resolve_conflicts(pending)
        prioritized = self._prioritize_tasks(resolved)

        available_minutes = constraints.get("available_minutes")
        next_open_minute = _time_to_minutes(constraints.get("start_time", "08:00"))
        used_minutes = 0

        schedule = Schedule(date=constraints.get("date", ""))
        for task in prioritized:
            if available_minutes is not None and used_minutes + task.duration_minutes > available_minutes:
                continue

            if task.preferred_time is not None:
                entry_start = _time_to_minutes(task.preferred_time)
                # reason = f"{task.priority} priority, honoring preferred time"
                reason = "honoring preferred time"
            else:
                entry_start = next_open_minute
                # reason = f"{task.priority} priority, next open slot"
                reason = "next open slot"

            entry_end = entry_start + task.duration_minutes
            schedule.add_entry(
                ScheduleEntry(
                    task=task,
                    start_time=_minutes_to_time(entry_start),
                    end_time=_minutes_to_time(entry_end),
                    reason=reason,
                )
            )
            next_open_minute = max(next_open_minute, entry_end)
            used_minutes += task.duration_minutes

        return schedule

    def explain_schedule(self, schedule: Schedule) -> str:
        """Return a human-readable summary of a schedule, including any skipped tasks."""
        lines = [f"Schedule for {schedule.date}:" if schedule.date else "Schedule:"]

        if not schedule.get_entries():
            lines.append("  (no tasks scheduled)")
        for entry in schedule.get_entries():
            lines.append(f"  {entry}")

        scheduled_ids = {entry.task.id for entry in schedule.get_entries()}
        skipped = [task for task in self.tasks if not task.completed and task.id not in scheduled_ids]
        if skipped:
            lines.append("Not scheduled (ran out of available time):")
            for task in skipped:
                # lines.append(f"  - {task.title} ({task.priority} priority, {task.duration_minutes} min)")
                lines.append(f"  - {task.title} ({task.duration_minutes} min)")

        return "\n".join(lines)

    def _prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks for scheduling: fixed-time tasks first, then shortest first."""
        return sorted(
            tasks,
            key=lambda task: (
                # PRIORITY_RANK.get(task.priority, len(PRIORITY_RANK)),  # priority disabled for now
                0 if task.preferred_time is not None else 1,
                task.duration_minutes,
            ),
        )

    def _resolve_conflicts(self, tasks: list[Task]) -> list[Task]:
        """Clear preferred_time on tasks that lose a same-slot conflict to another task."""
        claimed_times: dict[str, Task] = {}
        for task in tasks:
            if task.preferred_time is None:
                continue
            competitor = claimed_times.get(task.preferred_time)
            if competitor is None:
                claimed_times[task.preferred_time] = task
                continue
            # Two tasks want the same slot. Priority-based tie-breaking disabled for now
            # (re-enable this block when priority-based scheduling returns):
            # loser = task if PRIORITY_RANK.get(task.priority, 99) > PRIORITY_RANK.get(competitor.priority, 99) else competitor
            # if loser is competitor:
            #     claimed_times[task.preferred_time] = task
            # For now, first claim wins and the later task falls back to the next open slot.
            loser = task
            loser.preferred_time = None
        return tasks
