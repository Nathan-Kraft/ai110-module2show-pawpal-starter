import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Pet, Task


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
