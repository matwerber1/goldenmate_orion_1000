- use the checklists in docs/implementation_status.md to track implementation status of the phases and steps of each phase outlined in docs/implementation_plan.md as work is completed on this project.

- If you perform work that is not part of the implementation plan phases or steps, record this as an additional list item under a separate section titled "Unplanned work" in implementation_status.md. Each unplanned item should be summarized as a single clear and concise sentence.

- When you begin work on a phase or step from the implementation plan, update it's status in implementation_status.md to IN_PROGRESS.

- Create pytest tests for newly-added functionality.

- If a pytest test covers code that is part of an implementation phase, add a pytest marker that specifes which phase the tested code is part of.

- When you think you have finished the work for a phase, run all tests marked as covering code within that phase and any prior phases. A phase cannot be considered complete unless the current phase and all prior phase tests are passing.

- If you complete a phase or step from the implementation plan and all tests marked for that phase are passing, update it's status in implementation_status.md to PENDING_APPROVAL.

- Only mark a phase or its steps as COMPLETE if I explicitly tell you to do so.

- Before working on a phase, confirm that all prior phases are marked as COMPLETE. If a prior phase is not complete, do not proceed.

- When a python file is created or modified as part of an implementation phase, create or update an alphabetical list of affected files in that specific phase's section of the implementation status file.
