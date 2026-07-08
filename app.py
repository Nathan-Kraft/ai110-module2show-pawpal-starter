import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

Use this app as your interactive demo, connected to the Owner, Pet, Task, and Scheduler classes
in `pawpal_system.py`.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

"""
    )

# with st.expander("What you need to build", expanded=True):
#     st.markdown(
#         """
# At minimum, your system should:
# - Represent pet care tasks (what needs to happen, how long it takes, priority)
# - Represent the pet and the owner (basic info and preferences)
# - Build a plan/schedule for a day that chooses and orders tasks based on constraints
# - Explain the plan (why each task was chosen and when it happens)
# """
#     )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(id="owner-1", name=owner_name)
else:
    st.session_state.owner.name = owner_name
owner = st.session_state.owner

st.markdown("### Add a Pet")
col_pet1, col_pet2 = st.columns(2)
with col_pet1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_pet2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    pet_id = pet_name.strip().lower().replace(" ", "-")
    if not pet_id:
        st.error("Pet name can't be empty.")
    elif owner.get_pet(pet_id) is not None:
        st.warning(f"{pet_name} is already added.")
    else:
        owner.add_pet(Pet(id=pet_id, name=pet_name, species=species))
        st.success(f"Added {pet_name} ({species}).")

if owner.get_pets():
    st.write("Current pets:")
    st.table(
        [
            {"name": pet.name, "species": pet.species, "tasks": len(pet.get_tasks())}
            for pet in owner.get_pets()
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.markdown("### Tasks")
st.caption("Add a few tasks for a pet. These feed into the scheduler below.")

if owner.get_pets():
    pet_ids = [pet.id for pet in owner.get_pets()]
    pet_names_by_id = {pet.id: pet.name for pet in owner.get_pets()}
    selected_pet_id = st.selectbox("Pet", pet_ids, format_func=lambda pid: pet_names_by_id[pid])
    selected_pet = owner.get_pet(selected_pet_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")

    if st.button("Add task"):
        task_id = f"{selected_pet.id}-task-{len(selected_pet.get_tasks()) + 1}"
        selected_pet.add_task(
            Task(
                id=task_id,
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                pet_id=selected_pet.id,
                preferred_time=preferred_time.strip() or None,
            )
        )
        st.success(f"Added \"{task_title}\" for {selected_pet.name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        preview_scheduler = Scheduler()
        preview_scheduler.build_schedule(all_tasks, {"date": "Today"})
        prioritized_tasks = preview_scheduler.prioritize_tasks(preview_scheduler.pending_tasks)

        st.write("Current tasks (in scheduling order):")
        st.table(
            [
                {
                    "pet": task.pet_id,
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "preferred_time": task.preferred_time or "—",
                }
                for task in prioritized_tasks
            ]
        )

        for entry_a, entry_b, same_pet in preview_scheduler.conflicts:
            message = (
                f"Conflict: {entry_a.task.title} ({entry_a.start_time}-{entry_a.end_time}) "
                f"overlaps {entry_b.task.title} ({entry_b.start_time}-{entry_b.end_time})"
            )
            if same_pet:
                st.error(message + " — same pet, this can't actually happen.")
            else:
                st.warning(message + " — different pets, you'll need to be in two places at once.")
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet first before adding tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs the Scheduler over all pets' pending tasks and explains the result.")

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("No tasks to schedule yet. Add a pet and some tasks first.")
    else:
        scheduler = Scheduler()
        schedule = scheduler.build_schedule(all_tasks, {"date": "Today"})
        entries = schedule.get_entries()

        # Show the schedule itself as a table.
        if entries:
            schedule_rows = []
            for entry in entries:
                schedule_rows.append(
                    {
                        "start": entry.start_time,
                        "end": entry.end_time,
                        "pet": entry.task.pet_id,
                        "task": entry.task.title,
                        "priority": entry.task.priority,
                        "reason": entry.reason,
                    }
                )
            st.table(schedule_rows)
        else:
            st.info("No tasks fit into today's schedule.")

        # Tasks that didn't make it into the schedule.
        scheduled_task_ids = {entry.task.id for entry in entries}
        skipped_tasks = [task for task in scheduler.pending_tasks if task.id not in scheduled_task_ids]
        if skipped_tasks:
            skipped_descriptions = [
                f"{task.title} ({task.priority}, {task.duration_minutes} min)" for task in skipped_tasks
            ]
            st.warning("Not scheduled (ran out of available time): " + ", ".join(skipped_descriptions))

        # Any overlapping entries in the final schedule.
        conflicts = scheduler.find_conflicts(entries)
        for entry_a, entry_b, same_pet in conflicts:
            message = (
                f"Conflict: {entry_a.task.title} ({entry_a.start_time}-{entry_a.end_time}) overlaps "
                f"{entry_b.task.title} ({entry_b.start_time}-{entry_b.end_time})"
            )
            if same_pet:
                st.error(message + " — same pet, this can't actually happen.")
            else:
                st.warning(message + " — different pets, you'll need to be in two places at once.")

        if entries and not skipped_tasks and not conflicts:
            st.success("Schedule built with no conflicts and no skipped tasks.")
