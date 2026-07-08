# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initialUML design has four core classes plus two supporting classes: this being Owner, Pet, Task, Scheduler, and then schedule and scheduleEntry 

- What classes did you include, and what responsibilities did you assign to each?

Owner — Holds basic info (id, name, preferences) and manages a list of Pets (add_pet, get_pets). Responsible for representing the person, not any scheduling logic.

Pet — Holds id, name, species, and owns a list of Tasks (add_task, get_tasks). Acts as the link between an owner and the care tasks that apply to that specific pet.

Task —Is a data-only object representing one unit of pet care: title, duration_minutes, priority, preferred_time, and a completed flag with a mark_complete() method. Deliberately has no knowledge of scheduling or which pet it belongs to — it just describes "what" and "how urgent."

Scheduler — The only class with real behavior. Takes a list of Tasks and a constraints dict and produces a Schedule via build_schedule(), plus explains its choices via explain_schedule(). Kept separate from Owner/Pet so the scheduling algorithm can be built and tested independently of the data model.

Schedule / ScheduleEntry — We added these beyond the original four classes to separate "what a task is" from "when and why it happens today." Each ScheduleEntry pairs a Task with a start_time, end_time, and reason, so the scheduler can explain its plan without mutating the Task objects themselves.

A user should be able to 
1. add a pet
2. see and schedule todays tasks and create the master schedule. 
3. Is able to add and edit tasks

**b. Design changes**

- Did your design change during implementation?
Yes I made changes to task, and pet class. 

- If yes, describe at least one change and why you made it.
In the task class I added pet_id so that there is a back-reference so a flat list of tasks can be traced to its pet. I then added an if block to add_task to raise a ValueError if the task's pet_id doesn't match the pet its being added to. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)? 
My scheduler considers time, priority, date, available minutes, start time.

- How did you decide which constraints mattered most?

I treated them as a hierarchy rather than equally-weighted factors. Date/due_date comes first, since it's a hard eligibility filter, a task that isn't due yet shouldn't even be considered for today's schedule, regardless of how urgent it is otherwise. Once a task is eligible, priority decides ordering: high-priority tasks are placed (and, in `_prioritize_tasks` and `_resolve_conflicts`, win contested fixed-time slots) before lower-priority ones, so a full day drops the least important tasks first. Preferred time sits underneath priority. A fixed-time task is still honored at its requested time, but if two same-priority fixed tasks overlap, priority breaks the tie, and if they're tied on priority too, the earlier clock time wins so ordering stays predictable instead of depending on input order. Available_minutes and start_time are the outermost constraints, they don't affect ordering, just where placement starts and how much of the prioritized list actually fits before the day runs out.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
Conflict detection is decoupled from conflict resolution, and detection reports rather than repairs. find_conflicts runs against the raw requested times before _resolve_conflicts touches anything, purely to tell the caller "here's what had to be adjusted" it never rewrites the schedule itself. 
(Might have this fixed by the end) **CHECK THIS BEFORE SUBMISSION**
- Why is that tradeoff reasonable for this scenario?
the auto-repair on detection alternative was rejected in favor of transparency: the owner can see what got bumped and why, rather than the software silently making unreviewed decisions about pet care timing. 
An example of this is in the main.py demo output (the same time "vet checkup" conflict) that shows the tradeoff playing out. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI across most stages of the project: brainstorming the initial UML design (deciding whether Schedule/ScheduleEntry should be separate from Task), debugging (tracing why conflicts weren't being detected correctly), refactoring (cleaning up add_task once pet_id validation was added), and writing test cases for the scheduler.

- What kinds of prompts or questions were most helpful?
The most useful prompts were ones that asked "what's the tradeoff between X and Y" rather than "write me X" — for example, asking about auto-repair vs. report-only conflict handling surfaced the transparency tradeoff described in section 2b. Prompts framed as design questions pushed me to think about responsibilities and edge cases instead of just getting code handed to me.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
When I first asked for conflict handling, the AI's suggestion collapsed detection and repair into one step — resolve_conflicts would have rewritten preferred_time itself as it found overlaps. I pushed back because that meant the owner would never see what got bumped or why. I asked for it split the way it ended up: find_conflicts stays a pure reporter (used both pre-resolution on the raw requested times, and post-resolution in explain_schedule to surface anything still unresolved), while _resolve_conflicts is the only place that actually changes a task's preferred_time, and only for fixed-time tasks, by priority rank.

- How did you evaluate or verify what the AI suggested?
I traced _resolve_conflicts by hand against _sorted_fixed_tasks to confirm it only touches tasks with a preferred_time and never looks at same_pet when picking a winner — that distinction is reporting-only, surfaced in explain_schedule. I also confirmed find_conflicts never mutates its input by checking it's called twice (once on raw requested entries, once on final placed entries) and both calls return consistent, non-destructive results.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

I wrote a 58-test suite covering every class. For Task, I tested completion state changes, recurrence detection, and validation (invalid priority, invalid frequency, and non-positive duration all raise ValueError). For Pet, I tested add/remove/lookup, the pet_id-mismatch and duplicate-id guards on add_task, and the pending/completed split. For Owner, I tested flattening tasks across pets and filter_tasks by completion status and/or pet name. For Schedule/ScheduleEntry, I tested overlap detection (including that adjacent, non-overlapping entries are correctly NOT flagged), chronological sorting, and total scheduled minutes. For the Scheduler, I tested placement at preferred times vs. the next open slot, holding back tasks whose due_date hasn't arrived yet, the available_minutes budget (including exact-boundary and zero-budget cases, and confirming a shorter later task still gets scheduled after an earlier longer one is skipped), and priority-based ordering and conflict resolution — priority is the primary sort key ahead of duration and ahead of having a fixed preferred time, and when two preferred times overlap, the higher-priority task keeps its slot while the lower-priority one falls back to the next open slot.

The recurrence logic got the most dedicated coverage: completing a daily task advances due_date by one day and a weekly task by seven, completing a "once" task is a no-op, repeated completions correctly increment the occurrence id, and I specifically tested the fallback path where completed_on is omitted and due_date is None.

- Why were these tests important?

The scheduler has several places where a plausible implementation could quietly produce the wrong schedule without raising an error — skipping a task when the budget runs out but still scheduling a later, shorter one; silently producing a due_date of None instead of crashing when neither completed_on nor the original due_date is available; or letting a low-priority task win a time slot it shouldn't once priority-based scheduling went live. I prioritized tests around these over the happy path, and specifically added the priority tests once I re-enabled priority-based scheduling, since my first pass of tests predated that change and would have missed regressions there.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Fairly confident. Sorting, recurrence, conflict detection, and priority-based ordering/tie-breaking all have explicit tests and pass. I'm least confident about interactions between constraints when several apply at once — e.g., a fixed-time, high-priority task that also has a future due_date, combined with a tight available_minutes budget — since most of my tests exercise one or two constraints at a time rather than several stacked together.

- What edge cases would you test next if you had more time?

Exact-duplicate preferred_time strings (two tasks requesting the identical "09:00"), three or more overlapping preferred-time tasks with mixed priorities to confirm conflict resolution chains correctly rather than just handling pairs, a recurring task whose due_date lands on a leap day or year boundary, and combinations of priority + due_date + available_minutes constraints stacked on the same task set.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am most satisfied with learning more how to work with an AI for development. I also have enjoyed examining the AI responses and either being able to tell it when its wrong, or when its deciding to design the program a ceratain way that I don't like. I have really enjoyed getting its reasoning for its decisions and then critiquing or agreeing with it, but having the final say has been fun. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I'd redesign how `_resolve_conflicts` handles chains of three or more overlapping fixed-time tasks. Right now it only compares each task against the single currently-claimed slot, so I'm not fully confident it picks the right winner when three or more preferred times cascade into each other rather than just overlapping in pairs. I'd also want to stack constraints together in the scheduler itself (priority + due_date + available_minutes on the same task set) instead of testing them mostly one or two at a time, since that's the gap I flagged in section 4.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest thing I learned is that re-enabling a disabled feature (priority-based scheduling) is really a second implementation pass, not a formality. My first round of tests predated it and wouldn't have caught a regression if the priority logic had been wrong. That pushed me to trace the scheduler's tie-breaking by hand rather than trust that "the tests still pass" meant the new behavior was correct, which became my go-to way of evaluating AI suggestions generally: don't just run it, walk through what it does on a case you can verify yourself.
