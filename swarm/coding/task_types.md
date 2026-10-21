## Task types

Each task in a project must be of exactly one of the following types.

* Implementation
* Research
* Plan

<task_types_details>
<implementation>
These tasks tend to match 1-to-1 with commits into the git repository.
</implementation>

<research>
These tasks are about understanding the source code or context.
They won't result a change to the source's code (a "git commit").
Instead, a summary will be saved directly in the project plan
and details will be stored in a file under research/.

These tasks must begin with the word "Research":
<example>Task: Research existing canvas drag and swipe logic</example>
</research>

<plan>
These tasks are place holders for future work that will need to be done.
They are inserted when the exact nature of that work is not yet known
(for example, because it depends on the output of "research" tasks).
The text (under the task title) should describe the requirements.
In other words, it should specify what is to be accomplished
by the (pending) plan.

These tasks must begin with the word "Plan".
<example>Task: Plan how to modify the canvas class.</example>
</plan>
</task_types_details>
