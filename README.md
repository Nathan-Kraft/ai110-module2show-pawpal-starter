# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule
========================================
Schedule for 2026-07-05:
  08:00-08:30  Morning walk - honoring preferred time
  08:45-08:55  Feeding - honoring preferred time
  09:15-09:30  Litter box cleaning - honoring preferred time
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time`, `Scheduler._prioritize_tasks` | `sort_by_time` orders tasks chronologically by `preferred_time` (tasks with none sort last). `_prioritize_tasks` orders tasks for scheduling: fixed-time tasks first, then shortest-duration-first among the rest. |
| Filtering | `Owner.filter_tasks`, `Scheduler.build_schedule` | `filter_tasks` filters by completion status and/or pet name. `build_schedule` filters out completed tasks and tasks whose `due_date` hasn't arrived yet, and skips (via `continue`) any task that would exceed `available_minutes`. |
| Conflict handling | `Scheduler._resolve_conflicts`, `Scheduler.find_conflicts`, `Scheduler._sorted_fixed_tasks`, `Scheduler._requested_entries` | `_resolve_conflicts` sweeps fixed-time tasks chronologically and clears `preferred_time` on any task that overlaps an earlier-claimed slot, so double-booking never reaches the built schedule. `find_conflicts` is a separate diagnostic sweep that reports overlapping pairs (tagged same-pet vs. cross-pet); `build_schedule` runs it on the raw requested times *before* resolving them and stores the result in `self.conflicts`, so callers can see what had to be fixed. |
| Recurring tasks | `Task.is_recurring`, `Task.create_next_occurrence`, `Pet.complete_task`, `Pet._next_occurrence_id` | Tasks have a `frequency` (`"once"`/`"daily"`/`"weekly"`) and a `due_date`. `Pet.complete_task` marks a task done and, if it recurs, spawns the next occurrence with a new due date (+1 day for daily, +7 for weekly) and a unique id (`t1` → `t1#2` → `t1#3`, ...). `build_schedule` excludes any task whose `due_date` is still in the future. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
