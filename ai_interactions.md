# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Files modified:** pawpal_system.py, tests/test_pawpal.py

**What task did you give the agent?**
1. "Go through pawpal_system.py and uncomment and refactor the logic to implement priority into the logic"
2. "Does build_schedule or explain_schedule need refactoring to incorporate priority?"
3. "Scheduler is set to sort by priority first then by time?"
4. "Add this to the scheduler" (chronological tiebreak)
5. "Add a test for this change"



**What did the agent do?**
1. Re-enabled VALID_PRIORITIES + validation in Task.__post_init__; re-enabled PRIORITY_RANK; added priority into _place's reason strings; added priority to explain_schedule's skipped-task line; made _prioritize_tasks sort by priority rank first; made _resolve_conflicts let higher-priority tasks win contested fixed-time slots
2. Confirmed no — both already pick up priority through _prioritize_tasks/_resolve_conflicts/_place
3. Found it wasn't fully true — same-priority fixed-time tasks weren't chronologically ordered relative to each other, only grouped by "has preferred_time or not"
4. Added a third sort key to _prioritize_tasks — _time_to_minutes(task.preferred_time) (or inf if none) — placed between the fixed/flexible grouping and duration, so next_open_minute advances in a chronologically-consistent order for same-priority fixed tasks
5. Added test_build_schedule_orders_same_priority_fixed_tasks_chronologically in tests/test_pawpal.py




**What did you have to verify or fix manually?**
After the priority refactor, _place's two reason strings had been changed to include priority text (f"{task.priority} priority, honoring preferred time" / f"{task.priority} priority, next open slot"). I manually reverted just those two strings back to plain "honoring preferred time" / "next open slot" — the next_open_minute fallback branch's reason string no longer mentions priority, even though the parallel skipped-task line in explain_schedule still does.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
