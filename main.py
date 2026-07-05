"""Demo script: build an Owner with two Pets and a few Tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Schedule, ScheduleEntry, Scheduler, Task

owner = Owner(id="o1", name="Nick")

dog = Pet(id="p1", name="Biscuit", species="Dog")
cat = Pet(id="p2", name="Whiskers", species="Cat")
owner.add_pet(dog)
owner.add_pet(cat)

# Added out of chronological order on purpose, to exercise sort_by_time below.
cat.add_task(
    Task(
        id="t3",
        title="Litter box cleaning",
        duration_minutes=15,
        priority="medium",
        pet_id=cat.id,
        preferred_time="09:15",
    )
)
dog.add_task(
    Task(
        id="t2",
        title="Feeding",
        duration_minutes=10,
        priority="high",
        pet_id=dog.id,
        preferred_time="08:45",
    )
)
dog.add_task(
    Task(
        id="t1",
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        pet_id=dog.id,
        preferred_time="08:00",
    )
)
cat.add_task(
    Task(
        id="t4",
        title="Brushing",
        duration_minutes=10,
        priority="low",
        pet_id=cat.id,
    )
)
owner.get_pet("p1").get_task("t2").mark_complete()

scheduler = Scheduler()
constraints = {"date": "2026-07-05", "start_time": "08:00", "available_minutes": 120}
schedule = scheduler.build_schedule(owner.get_all_tasks(), constraints)

print("Today's Schedule")
print("=" * 40)
print(scheduler.explain_schedule(schedule))

print("\nAll tasks sorted by time")
print("=" * 40)
for task in scheduler.sort_by_time(owner.get_all_tasks()):
    time_label = task.preferred_time if task.preferred_time is not None else "no preferred time"
    print(f"  {time_label:>17}  {task.title} ({dog.name if task.pet_id == dog.id else cat.name})")

print("\nBiscuit's pending tasks (filter by pet name + completion status)")
print("=" * 40)
for task in owner.filter_tasks(completed=False, pet_name="Biscuit"):
    print(f"  {task.title}")

print("\nAll completed tasks (filter by completion status only)")
print("=" * 40)
for task in owner.filter_tasks(completed=True):
    print(f"  {task.title}")

# Two tasks requested for the exact same time slot, for different pets. build_schedule's
# conflict resolution catches this *before* scheduling: the later-starting one loses its
# preferred_time and falls back to the next open slot instead of double-booking the owner.
cat.add_task(
    Task(
        id="t5",
        title="Vet checkup",
        duration_minutes=45,
        priority="high",
        pet_id=cat.id,
        preferred_time="08:00",  # same slot as Biscuit's "Morning walk"
    )
)
same_time_schedule = scheduler.build_schedule(owner.get_all_tasks(), constraints)
print("\nSchedule after adding a same-time-slot conflict (resolved automatically)")
print("=" * 40)
print(scheduler.explain_schedule(same_time_schedule))
print(f"  -> conflicts detected by the scheduler: {len(scheduler.conflicts)}")

# To see the warning path itself fire, build a Schedule directly with two entries that
# truly overlap (bypassing build_schedule's own conflict resolution).
conflicting_schedule = Schedule(date="2026-07-05")
conflicting_schedule.add_entry(ScheduleEntry(task=dog.get_task("t1"), start_time="08:00", end_time="08:30", reason="fixed"))
conflicting_schedule.add_entry(ScheduleEntry(task=cat.get_task("t5"), start_time="08:15", end_time="09:00", reason="fixed"))
print("\nManually-built overlapping schedule (exercises the conflict warning)")
print("=" * 40)
print(scheduler.explain_schedule(conflicting_schedule))
