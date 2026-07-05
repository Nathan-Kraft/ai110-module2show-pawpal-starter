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

- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

- How did you evaluate or verify what the AI suggested?


---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
