"""PawPal+ system classes: Owner, Pet, Task, Scheduler.

Skeleton only — mirrors diagrams/uml_draft.mmd. Scheduling logic is not implemented yet.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta


def _time_to_minutes(time_str: str) -> int:
    """Convert an "HH:MM" string into minutes since midnight."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight into an "HH:MM" string."""
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _advance_date(date_str: str, days: int) -> str:
    """Return the "YYYY-MM-DD" date `days` days after the given "YYYY-MM-DD" date."""
    return (date.fromisoformat(date_str) + timedelta(days=days)).isoformat()


VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"once", "daily", "weekly"}
FREQUENCY_INTERVAL_DAYS = {"daily": 1, "weekly": 7}


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
    due_date: str | None = None  # "YYYY-MM-DD"; None means always available to schedule

    def __post_init__(self) -> None:
        """Validate priority, frequency, and duration after the dataclass fields are set."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got {self.priority!r}")
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

    def create_next_occurrence(self, new_id: str, due_date: str | None = None) -> "Task":
        """Return a new pending Task representing this recurring task's next occurrence."""
        return Task(
            id=new_id,
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_id=self.pet_id,
            description=self.description,
            frequency=self.frequency,
            preferred_time=self.preferred_time,
            completed=False,
            due_date=due_date,
        )


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

    def complete_task(self, task_id: str, completed_on: str | None = None) -> Task | None:
        """Mark the given task complete, spawning its next occurrence if it recurs.

        `completed_on` ("YYYY-MM-DD") is the date the task was completed on, used to compute
        the next occurrence's due_date (+1 day for "daily", +7 days for "weekly"). If omitted,
        the completed task's own due_date is used as the base instead; if neither is available,
        the next occurrence gets no due_date and remains always available to schedule.

        Returns the newly spawned occurrence, or None if the task wasn't found or
        doesn't recur (frequency "once").
        """
        task = self.get_task(task_id)
        if task is None:
            return None
        task.mark_complete()
        if not task.is_recurring():
            return None

        base_date = completed_on or task.due_date
        next_due_date = (
            _advance_date(base_date, FREQUENCY_INTERVAL_DAYS[task.frequency])
            if base_date is not None
            else None
        )
        next_task = task.create_next_occurrence(self._next_occurrence_id(task.id), due_date=next_due_date)
        self.add_task(next_task)
        return next_task

    def _next_occurrence_id(self, base_id: str) -> str:
        """Generate a task id for a recurring task's next occurrence, unique within this pet."""
        root = base_id.split("#", 1)[0]
        n = 2
        while self.get_task(f"{root}#{n}") is not None:
            n += 1
        return f"{root}#{n}"

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

    def filter_tasks(self, completed: bool | None = None, pet_name: str | None = None) -> list[Task]:
        """Return this owner's tasks matching the given completion status and/or pet name.

        Either filter may be omitted (left as None) to match tasks regardless of that
        criterion; when both are given, a task must satisfy both to be included.
        """
        pet_ids = None
        if pet_name is not None:
            pet_ids = {pet.id for pet in self.pets if pet.name == pet_name}

        return [
            task
            for task in self.get_all_tasks()
            if (completed is None or task.completed == completed)
            and (pet_ids is None or task.pet_id in pet_ids)
        ]


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


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """Builds a Schedule from a list of Tasks given constraints.

    Constraints supported:
      - "date": str, stamped onto the resulting Schedule; also used to hold back recurring
        tasks whose due_date hasn't arrived yet (tasks with no due_date are always eligible)
      - "start_time": "HH:MM", when the day's schedule begins (default "08:00")
      - "available_minutes": int | None, total time budget for the day (default None = unlimited)
    """

    def __init__(self) -> None:
        """Initialize an empty Scheduler; state is populated by build_schedule."""
        self.tasks: list[Task] = []
        self.pending_tasks: list[Task] = []
        self.conflicts: list[tuple["ScheduleEntry", "ScheduleEntry", bool]] = []

    def build_schedule(self, tasks: list[Task], constraints: dict) -> Schedule:
        """Build a Schedule for the given tasks, respecting the given constraints."""
        self.tasks = list(tasks)
        date = constraints.get("date", "")
        pending = [
            task
            for task in self.tasks
            if not task.completed and (task.due_date is None or not date or task.due_date <= date)
        ]
        self.pending_tasks = pending
        sorted_fixed_tasks = self._sorted_fixed_tasks(pending)

        # Detect conflicts among the raw requested times before _resolve_conflicts adjusts
        # anything, so callers can see what the scheduler had to fix. Reuses the same
        # chronological sort _resolve_conflicts needs, instead of each sorting separately.
        self.conflicts = self.find_conflicts(self._requested_entries(sorted_fixed_tasks))

        resolved = self._resolve_conflicts(pending, sorted_fixed_tasks)
        prioritized = self._prioritize_tasks(resolved)

        available_minutes = constraints.get("available_minutes")
        next_open_minute = _time_to_minutes(constraints.get("start_time", "08:00"))
        used_minutes = 0

        schedule = Schedule(date=date)
        for task in prioritized:
            if available_minutes is not None and used_minutes + task.duration_minutes > available_minutes:
                continue

            entry_start, reason = self._place(task, next_open_minute)
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

    def _sorted_fixed_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks that have a preferred_time, sorted chronologically by it.

        Shared by find_conflicts (via _requested_entries) and _resolve_conflicts so both
        operate on the same chronological ordering without each sorting independently.
        """
        return sorted(
            (task for task in tasks if task.preferred_time is not None),
            key=lambda task: _time_to_minutes(task.preferred_time),
        )

    def _requested_entries(self, sorted_fixed_tasks: list[Task]) -> list[ScheduleEntry]:
        """Build ScheduleEntry stand-ins for each fixed-time task's originally requested slot.

        Used to run find_conflicts on what was actually asked for, before _resolve_conflicts
        clears preferred_time on any losing task. Expects tasks already sorted chronologically
        (see _sorted_fixed_tasks).
        """
        return [
            ScheduleEntry(
                task=task,
                start_time=task.preferred_time,
                end_time=_minutes_to_time(_time_to_minutes(task.preferred_time) + task.duration_minutes),
                reason="requested time",
            )
            for task in sorted_fixed_tasks
        ]

    def _place(self, task: Task, next_open_minute: int) -> tuple[int, str]:
        """Return (start_minute, reason): a task's preferred time if it has one, else the next open slot."""
        if task.preferred_time is not None:
            return _time_to_minutes(task.preferred_time), f"{task.priority} priority, honoring preferred time"
        return next_open_minute, f"{task.priority} priority, next open slot"

    def explain_schedule(self, schedule: Schedule) -> str:
        """Return a human-readable summary of a schedule, including any skipped tasks."""
        entries = schedule.get_entries()
        lines = [f"Schedule for {schedule.date}:" if schedule.date else "Schedule:"]

        if not entries:
            lines.append("  (no tasks scheduled)")
        for entry in entries:
            lines.append(f"  {entry}")

        scheduled_ids = {entry.task.id for entry in entries}
        skipped = [task for task in self.pending_tasks if task.id not in scheduled_ids]
        if skipped:
            lines.append("Not scheduled (ran out of available time):")
            for task in skipped:
                lines.append(f"  - {task.title} ({task.priority} priority, {task.duration_minutes} min)")

        conflicts = self.find_conflicts(entries)
        if conflicts:
            lines.append("Conflicts detected:")
            for entry_a, entry_b, same_pet in conflicts:
                scope = "same pet" if same_pet else "different pets"
                lines.append(
                    f"  - {entry_a.task.title} ({entry_a.start_time}-{entry_a.end_time}) overlaps "
                    f"{entry_b.task.title} ({entry_b.start_time}-{entry_b.end_time}) [{scope}]"
                )

        return "\n".join(lines)

    def find_conflicts(self, entries: list[ScheduleEntry]) -> list[tuple[ScheduleEntry, ScheduleEntry, bool]]:
        """Return all pairs of entries whose time ranges overlap.

        `entries` must be sorted by start time (as returned by Schedule.get_entries()).
        Sweeps through them in order, comparing each entry only against the still-open
        entries that could plausibly overlap it, instead of checking every pair.

        Each result is (entry_a, entry_b, same_pet), where same_pet is True when both
        entries belong to the same pet (a same-pet overlap means one task literally can't
        happen while the other is happening; a cross-pet overlap means the owner would
        need to be in two places for two different pets at once).
        """
        conflicts = []
        open_entries: list[ScheduleEntry] = []
        for entry in entries:
            start = _time_to_minutes(entry.start_time)
            open_entries = [other for other in open_entries if _time_to_minutes(other.end_time) > start]
            for other in open_entries:
                same_pet = other.task.pet_id == entry.task.pet_id
                conflicts.append((other, entry, same_pet))
            open_entries.append(entry)
        return conflicts

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by preferred_time; tasks with no preferred_time sort last."""
        return sorted(
            tasks,
            key=lambda task: _time_to_minutes(task.preferred_time) if task.preferred_time is not None else float("inf"),
        )

    def _prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks for scheduling: highest priority first, then fixed-time tasks
        chronologically, then shortest first."""
        return sorted(
            tasks,
            key=lambda task: (
                PRIORITY_RANK.get(task.priority, len(PRIORITY_RANK)),
                0 if task.preferred_time is not None else 1,
                _time_to_minutes(task.preferred_time) if task.preferred_time is not None else float("inf"),
                task.duration_minutes,
            ),
        )

    def _resolve_conflicts(self, tasks: list[Task], sorted_fixed_tasks: list[Task]) -> list[Task]:
        """Clear preferred_time on tasks whose fixed slot overlaps an earlier-claimed one.

        `sorted_fixed_tasks` (see _sorted_fixed_tasks) holds the fixed-time subset of `tasks`
        chronologically, so overlap (not just an exact same-string start time) is caught.
        """
        claimed_until: int | None = None
        claimant: Task | None = None
        for task in sorted_fixed_tasks:
            start = _time_to_minutes(task.preferred_time)
            if claimed_until is None or start >= claimed_until:
                claimed_until = start + task.duration_minutes
                claimant = task
                continue
            # This task's slot overlaps the previously claimed one; the higher-priority
            # task keeps its preferred time, and the other falls back to the next open slot.
            if PRIORITY_RANK.get(task.priority, 99) < PRIORITY_RANK.get(claimant.priority, 99):
                claimant.preferred_time = None
                claimed_until = start + task.duration_minutes
                claimant = task
            else:
                task.preferred_time = None
        return tasks
    
