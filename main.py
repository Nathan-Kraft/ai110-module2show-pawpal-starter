"""Demo script: build an Owner with two Pets and a few Tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task

owner = Owner(id="o1", name="Nick")

dog = Pet(id="p1", name="Biscuit", species="Dog")
cat = Pet(id="p2", name="Whiskers", species="Cat")
owner.add_pet(dog)
owner.add_pet(cat)

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

scheduler = Scheduler()
constraints = {"date": "2026-07-05", "start_time": "08:00", "available_minutes": 120}
schedule = scheduler.build_schedule(owner.get_all_tasks(), constraints)

print("Today's Schedule")
print("=" * 40)
print(scheduler.explain_schedule(schedule))
