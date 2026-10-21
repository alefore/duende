## Project Plan file

A project plan is stored inside a file called `plan.md`.
It is associated with a specific project to improve a software product.

<structure>
It has the following sections:

* "## Goal": the description of the project's goal.

* "## Task: XXXX": Information about a specific task that should be executed.
</structure>

<tasks>
Each task contains a title summarizing it
(e.g., "Add optional parameter foo to function Bar").
Task title's are unique across the entire project plan.

The title is followed by a text description of what the task entails.
Titles can contain a state description: "(done)" or "(obsolete)"
</tasks>

<attempts>
A task section will contain an `### Attempt` subsection
for each attempt made to implement it.
Each attempt title includes the number of attempt explicitly (1, 2...),
followed by the state: Implement, Fail, Success, Review, Improve, Commit:

* Implement: An agent is actively working on this attempt.
  <example>### Attempt 4: Ongoing</example>

* Fail: An agent has failed to accomplish the attempt.
  The title must include a short description of why it failed:
  <example>### Attempt 1: Fail: Problems with LazyString API</example>
  The contents of the section MUST list a bit of details about the problems.
  If you have compiler or test output (or anything else worth storing),
  save it to a new file in `data/` and reference that file here
  (see example below).

* Success: The task has been accomplished.
  If a commit has been made to the git repository,
  it should be mentioned in the title:
  <example>### Attempt 2: Success: f456ab38</example>

* Review: An agent believes that the task has been accomplished,
  but review for code-quality and consistency is still required
  (which is usually done by a separate agent).
  <example>### Attempt 1: Needs Review</example>

* Improve: An agent has reviewed the task's implementation
  and determined that the code quality is insufficient.
  In this case, specific improvements are listed inside
  <improvement>...</improvement> tags
  (in the `### Attempt: Improve` section).

* Commit: The task is accomplished,
  but the changes still need to be commited
  (to the git repository `$PROJECT_DIR/repository/`).

<example>
    ## Task: Add optional parameter foo (done).

    Text description of what the task entails.

    ### Attempt 1: Fail: Problems with LazyString API

    Attempts to modify file foo.cc failed.
    We struggled significantly to extend the function quux,
    due to the API for the "LazyString" class being unknown.

    ### Attempt 2: Fail: Unrelated compilation error

    Attempts to modify file foo.cc succeeded.
    However, we got stuck trying to fix an unrelated compilation error.

    Details: `data/parameter_failure_foo_12.md`

    ### Attempt 3: Improve

    The following improvements are needed:

    <improvement>...</improvement>
    <improvement>...</improvement>

    ### Attempt 4: Success: df943d92
</example>
</attempts>

<states>
A task can done or obsolete, which is stated explicitly in the title:

* *Done*: An attempt succeeded! The title MUST include the string "(done)".
  <example>## Task: Add parameter (done)</example>

* *Obsolete*: Task has been abandoned and must be ignored.
  <example>## Task: Add parameter (obsolete)</example>

Tasks that are neither done nor obsolete are said to be *pending*.
</states>
