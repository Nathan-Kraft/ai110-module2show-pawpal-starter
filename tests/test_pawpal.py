import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Schedule, ScheduleEntry, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task(id="t1", title="Morning walk", duration_minutes=30, priority="high", pet_id="p1")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    assert len(pet.get_tasks()) == 0

    task = Task(id="t1", title="Morning walk", duration_minutes=30, priority="high", pet_id="p1")
    pet.add_task(task)

    assert len(pet.get_tasks()) == 1


# --- Task -------------------------------------------------------------------


def test_mark_incomplete_resets_task_status():
    task = Task(id="t1", title="Morning walk", duration_minutes=30, priority="high", pet_id="p1")
    task.mark_complete()

    task.mark_incomplete()

    assert task.completed is False


def test_is_recurring_false_for_once():
    task = Task(id="t1", title="Vet visit", duration_minutes=30, priority="high", pet_id="p1", frequency="once")
    assert task.is_recurring() is False


def test_is_recurring_true_for_daily_and_weekly():
    daily = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="daily")
    weekly = Task(id="t2", title="Groom", duration_minutes=20, priority="low", pet_id="p1", frequency="weekly")
    assert daily.is_recurring() is True
    assert weekly.is_recurring() is True


def test_invalid_frequency_raises():
    with pytest.raises(ValueError):
        Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="monthly")


@pytest.mark.parametrize("duration", [0, -5])
def test_non_positive_duration_raises(duration):
    with pytest.raises(ValueError):
        Task(id="t1", title="Feed", duration_minutes=duration, priority="low", pet_id="p1")


def test_create_next_occurrence_copies_fields_and_resets_completion():
    task = Task(
        id="t1",
        title="Feed",
        duration_minutes=10,
        priority="low",
        pet_id="p1",
        description="Wet food",
        frequency="daily",
        preferred_time="08:00",
    )
    task.mark_complete()

    next_task = task.create_next_occurrence("t1#2", due_date="2026-01-02")

    assert next_task.id == "t1#2"
    assert next_task.title == task.title
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.description == task.description
    assert next_task.frequency == task.frequency
    assert next_task.preferred_time == task.preferred_time
    assert next_task.completed is False
    assert next_task.due_date == "2026-01-02"


# --- Pet ---------------------------------------------------------------------


def test_add_task_mismatched_pet_id_raises():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="wrong")

    with pytest.raises(ValueError):
        pet.add_task(task)


def test_add_task_duplicate_id_raises():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))

    with pytest.raises(ValueError):
        pet.add_task(Task(id="t1", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))


def test_remove_task_removes_matching_task_only():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))
    pet.add_task(Task(id="t2", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))

    pet.remove_task("t1")

    assert pet.get_task("t1") is None
    assert pet.get_task("t2") is not None


def test_remove_task_missing_id_is_noop():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))

    pet.remove_task("does-not-exist")

    assert len(pet.get_tasks()) == 1


def test_get_task_returns_none_when_missing():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    assert pet.get_task("nope") is None


def test_get_pending_and_completed_tasks_split_correctly():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))
    pet.add_task(Task(id="t2", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))
    pet.get_task("t1").mark_complete()

    assert [task.id for task in pet.get_pending_tasks()] == ["t2"]
    assert [task.id for task in pet.get_completed_tasks()] == ["t1"]


def test_total_duration_minutes_sums_all_tasks():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))
    pet.add_task(Task(id="t2", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))

    assert pet.total_duration_minutes() == 30


def test_complete_task_once_frequency_returns_none_and_marks_complete():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Vet visit", duration_minutes=30, priority="high", pet_id="p1", frequency="once"))

    result = pet.complete_task("t1")

    assert result is None
    assert pet.get_task("t1").completed is True
    assert len(pet.get_tasks()) == 1


def test_complete_task_missing_id_returns_none():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    assert pet.complete_task("nope") is None


def test_complete_task_daily_spawns_next_occurrence_with_advanced_due_date():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(
        Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="daily", due_date="2026-01-01")
    )

    next_task = pet.complete_task("t1", completed_on="2026-01-01")

    assert next_task is not None
    assert next_task.id == "t1#2"
    assert next_task.due_date == "2026-01-02"
    assert next_task.completed is False
    assert pet.get_task("t1").completed is True


def test_complete_task_weekly_advances_seven_days():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(
        Task(id="t1", title="Groom", duration_minutes=30, priority="low", pet_id="p1", frequency="weekly", due_date="2026-01-01")
    )

    next_task = pet.complete_task("t1", completed_on="2026-01-01")

    assert next_task.due_date == "2026-01-08"


def test_complete_task_uses_due_date_when_completed_on_omitted():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(
        Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="daily", due_date="2026-01-05")
    )

    next_task = pet.complete_task("t1")

    assert next_task.due_date == "2026-01-06"


def test_complete_task_with_no_due_date_and_no_completed_on_keeps_due_date_none():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="daily"))

    next_task = pet.complete_task("t1")

    assert next_task.due_date is None


def test_complete_task_month_boundary_rolls_over():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(
        Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="weekly", due_date="2026-01-28")
    )

    next_task = pet.complete_task("t1", completed_on="2026-01-28")

    assert next_task.due_date == "2026-02-04"


def test_complete_task_repeated_cycles_increment_occurrence_suffix():
    pet = Pet(id="p1", name="Biscuit", species="Dog")
    pet.add_task(
        Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", frequency="daily", due_date="2026-01-01")
    )

    second = pet.complete_task("t1", completed_on="2026-01-01")
    third = pet.complete_task(second.id, completed_on=second.due_date)

    assert second.id == "t1#2"
    assert third.id == "t1#3"


# --- Owner -------------------------------------------------------------------


def test_add_pet_duplicate_id_raises():
    owner = Owner(id="o1", name="Alex")
    owner.add_pet(Pet(id="p1", name="Biscuit", species="Dog"))

    with pytest.raises(ValueError):
        owner.add_pet(Pet(id="p1", name="Waffles", species="Cat"))


def test_remove_pet_removes_matching_pet_only():
    owner = Owner(id="o1", name="Alex")
    owner.add_pet(Pet(id="p1", name="Biscuit", species="Dog"))
    owner.add_pet(Pet(id="p2", name="Waffles", species="Cat"))

    owner.remove_pet("p1")

    assert owner.get_pet("p1") is None
    assert owner.get_pet("p2") is not None


def test_get_all_tasks_flattens_across_pets():
    owner = Owner(id="o1", name="Alex")
    biscuit = Pet(id="p1", name="Biscuit", species="Dog")
    waffles = Pet(id="p2", name="Waffles", species="Cat")
    biscuit.add_task(Task(id="t1", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))
    waffles.add_task(Task(id="t2", title="Feed", duration_minutes=10, priority="low", pet_id="p2"))
    owner.add_pet(biscuit)
    owner.add_pet(waffles)

    all_tasks = owner.get_all_tasks()

    assert {task.id for task in all_tasks} == {"t1", "t2"}


def test_owner_get_pending_and_completed_across_pets():
    owner = Owner(id="o1", name="Alex")
    biscuit = Pet(id="p1", name="Biscuit", species="Dog")
    biscuit.add_task(Task(id="t1", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))
    biscuit.add_task(Task(id="t2", title="Feed", duration_minutes=10, priority="low", pet_id="p1"))
    biscuit.get_task("t1").mark_complete()
    owner.add_pet(biscuit)

    assert [task.id for task in owner.get_pending_tasks()] == ["t2"]
    assert [task.id for task in owner.get_completed_tasks()] == ["t1"]


def test_filter_tasks_by_completed_and_pet_name():
    owner = Owner(id="o1", name="Alex")
    biscuit = Pet(id="p1", name="Biscuit", species="Dog")
    waffles = Pet(id="p2", name="Waffles", species="Cat")
    biscuit.add_task(Task(id="t1", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))
    waffles.add_task(Task(id="t2", title="Feed", duration_minutes=10, priority="low", pet_id="p2"))
    biscuit.get_task("t1").mark_complete()
    owner.add_pet(biscuit)
    owner.add_pet(waffles)

    assert [task.id for task in owner.filter_tasks(completed=True)] == ["t1"]
    assert [task.id for task in owner.filter_tasks(pet_name="Waffles")] == ["t2"]
    assert owner.filter_tasks(completed=True, pet_name="Waffles") == []
    assert len(owner.filter_tasks()) == 2


def test_filter_tasks_unknown_pet_name_returns_empty():
    owner = Owner(id="o1", name="Alex")
    biscuit = Pet(id="p1", name="Biscuit", species="Dog")
    biscuit.add_task(Task(id="t1", title="Walk", duration_minutes=20, priority="low", pet_id="p1"))
    owner.add_pet(biscuit)

    assert owner.filter_tasks(pet_name="Ghost") == []


# --- ScheduleEntry / Schedule --------------------------------------------------


def _entry(task_id, pet_id, start, end, title="Task"):
    task = Task(id=task_id, title=title, duration_minutes=1, priority="low", pet_id=pet_id)
    return ScheduleEntry(task=task, start_time=start, end_time=end, reason="test")


def test_schedule_entry_duration_minutes():
    entry = _entry("t1", "p1", "08:00", "08:30")
    assert entry.duration_minutes() == 30


def test_schedule_entry_overlaps_true_for_overlapping_ranges():
    a = _entry("t1", "p1", "08:00", "09:00")
    b = _entry("t2", "p1", "08:30", "09:30")
    assert a.overlaps(b) is True
    assert b.overlaps(a) is True


def test_schedule_entry_overlaps_false_for_adjacent_ranges():
    a = _entry("t1", "p1", "08:00", "09:00")
    b = _entry("t2", "p1", "09:00", "10:00")
    assert a.overlaps(b) is False


def test_schedule_get_entries_sorted_chronologically():
    schedule = Schedule(date="2026-01-01")
    schedule.add_entry(_entry("t1", "p1", "10:00", "10:30", title="Later"))
    schedule.add_entry(_entry("t2", "p1", "08:00", "08:30", title="Earlier"))

    ordered = schedule.get_entries()

    assert [entry.task.title for entry in ordered] == ["Earlier", "Later"]


def test_schedule_total_scheduled_minutes():
    schedule = Schedule(date="2026-01-01")
    schedule.add_entry(_entry("t1", "p1", "08:00", "08:30"))
    schedule.add_entry(_entry("t2", "p1", "09:00", "09:15"))

    assert schedule.total_scheduled_minutes() == 45


def test_schedule_find_entry_for_task():
    schedule = Schedule(date="2026-01-01")
    schedule.add_entry(_entry("t1", "p1", "08:00", "08:30"))

    assert schedule.find_entry_for_task("t1") is not None
    assert schedule.find_entry_for_task("missing") is None


# --- Scheduler ----------------------------------------------------------------


def test_build_schedule_places_task_at_start_time():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"start_time": "08:00"})

    entries = schedule.get_entries()
    assert len(entries) == 1
    assert entries[0].start_time == "08:00"
    assert entries[0].end_time == "08:10"


def test_build_schedule_honors_preferred_time():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", preferred_time="09:00")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"start_time": "08:00"})

    entry = schedule.find_entry_for_task("t1")
    assert entry.start_time == "09:00"


def test_build_schedule_excludes_completed_tasks():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1")
    task.mark_complete()
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {})

    assert schedule.get_entries() == []


def test_build_schedule_holds_back_future_due_dates():
    future_task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", due_date="2026-02-01")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([future_task], {"date": "2026-01-01"})

    assert schedule.get_entries() == []


def test_build_schedule_includes_task_due_today():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1", due_date="2026-01-01")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"date": "2026-01-01"})

    assert len(schedule.get_entries()) == 1


def test_build_schedule_includes_task_with_no_due_date_regardless_of_date():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"date": "2026-01-01"})

    assert len(schedule.get_entries()) == 1


def test_build_schedule_respects_available_minutes_budget():
    tasks = [
        Task(id="t1", title="Long", duration_minutes=40, priority="low", pet_id="p1"),
        Task(id="t2", title="Short", duration_minutes=10, priority="low", pet_id="p1"),
    ]
    scheduler = Scheduler()

    schedule = scheduler.build_schedule(tasks, {"available_minutes": 30, "start_time": "08:00"})

    scheduled_ids = {entry.task.id for entry in schedule.get_entries()}
    assert scheduled_ids == {"t2"}


def test_build_schedule_boundary_available_minutes_still_fits():
    task = Task(id="t1", title="Feed", duration_minutes=30, priority="low", pet_id="p1")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"available_minutes": 30})

    assert len(schedule.get_entries()) == 1


def test_build_schedule_zero_available_minutes_schedules_nothing():
    task = Task(id="t1", title="Feed", duration_minutes=10, priority="low", pet_id="p1")
    scheduler = Scheduler()

    schedule = scheduler.build_schedule([task], {"available_minutes": 0})

    assert schedule.get_entries() == []


def test_build_schedule_resolves_overlapping_preferred_times():
    tasks = [
        Task(id="t1", title="First", duration_minutes=60, priority="low", pet_id="p1", preferred_time="09:00"),
        Task(id="t2", title="Second", duration_minutes=30, priority="low", pet_id="p1", preferred_time="09:15"),
    ]
    scheduler = Scheduler()

    schedule = scheduler.build_schedule(tasks, {"start_time": "08:00"})

    first_entry = schedule.find_entry_for_task("t1")
    second_entry = schedule.find_entry_for_task("t2")
    assert first_entry.start_time == "09:00"
    assert not first_entry.overlaps(second_entry)


def test_build_schedule_orders_same_priority_fixed_tasks_chronologically():
    tasks = [
        Task(id="t_later", title="Later", duration_minutes=20, priority="medium", pet_id="p1", preferred_time="10:00"),
        Task(id="t_earlier", title="Earlier", duration_minutes=20, priority="medium", pet_id="p1", preferred_time="09:00"),
    ]
    scheduler = Scheduler()

    schedule = scheduler.build_schedule(tasks, {"available_minutes": 20, "start_time": "08:00"})

    scheduled_ids = {entry.task.id for entry in schedule.get_entries()}
    assert scheduled_ids == {"t_earlier"}


def test_sort_by_time_puts_tasks_without_preferred_time_last():
    tasks = [
        Task(id="t1", title="No time", duration_minutes=10, priority="low", pet_id="p1"),
        Task(id="t2", title="Morning", duration_minutes=10, priority="low", pet_id="p1", preferred_time="07:00"),
    ]
    scheduler = Scheduler()

    ordered = scheduler.sort_by_time(tasks)

    assert [task.id for task in ordered] == ["t2", "t1"]


def test_find_conflicts_detects_overlap_and_pet_scope():
    same_pet_a = _entry("t1", "p1", "08:00", "09:00")
    same_pet_b = _entry("t2", "p1", "08:30", "09:30")
    scheduler = Scheduler()

    conflicts = scheduler.find_conflicts([same_pet_a, same_pet_b])

    assert len(conflicts) == 1
    assert conflicts[0][2] is True


def test_find_conflicts_cross_pet_marked_as_not_same_pet():
    entry_a = _entry("t1", "p1", "08:00", "09:00")
    entry_b = _entry("t2", "p2", "08:30", "09:30")
    scheduler = Scheduler()

    conflicts = scheduler.find_conflicts([entry_a, entry_b])

    assert len(conflicts) == 1
    assert conflicts[0][2] is False


def test_find_conflicts_no_overlap_returns_empty():
    entry_a = _entry("t1", "p1", "08:00", "09:00")
    entry_b = _entry("t2", "p1", "09:00", "10:00")
    scheduler = Scheduler()

    assert scheduler.find_conflicts([entry_a, entry_b]) == []


def test_explain_schedule_lists_skipped_tasks():
    tasks = [
        Task(id="t1", title="Long", duration_minutes=40, priority="low", pet_id="p1"),
        Task(id="t2", title="Short", duration_minutes=10, priority="low", pet_id="p1"),
    ]
    scheduler = Scheduler()
    schedule = scheduler.build_schedule(tasks, {"available_minutes": 30})

    summary = scheduler.explain_schedule(schedule)

    assert "Not scheduled" in summary
    assert "Long" in summary


def test_explain_schedule_no_tasks_scheduled_message():
    scheduler = Scheduler()
    schedule = scheduler.build_schedule([], {"date": "2026-01-01"})

    summary = scheduler.explain_schedule(schedule)

    assert "(no tasks scheduled)" in summary
