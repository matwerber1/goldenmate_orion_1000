- use the checklists in docs/implementation_status.md to track implementation status of the phases and steps of each phase outlined in docs/implementation_plan.md as work is completed on this project.

- If you perform work that is not part of the implementation plan phases or steps, record this as an additional list item under a separate section titled "Unplanned work" in implementation_status.md. Each unplanned item should be summarized as a single clear and concise sentence.

- When you begin work on a phase or step from the implementation plan, update it's status in implementation_status.md to IN_PROGRESS.

- Create and use pytest to validate that newly-added or modified code is working as expected.

- If a pytest test covers code that is part of an implementation phase, add a pytest marker that specifes which phase the tested code is part of.

- When you think you have finished the work for a phase, re-run all pytest tests across the entire project and confirm they are passing before considering a phase complete.

- If you complete a phase or step from the implementation plan and all tests marked for that phase are passing, update it's status in implementation_status.md to PENDING_APPROVAL.

- Only mark a phase or its steps as APPROVED if I explicitly tell you to do so.

- Before working on a phase, confirm that all prior phases are marked as APPROVED. If a prior phase is not marked as APPROVED, do not proceed.

- When a python file is created or modified as part of an implementation phase, create or update an alphabetical list of affected files in that specific phase's section of the implementation status file.

- when beginning or resuming work on a phase from the implementation plan, review the project plan (project_plan.md)

- if pytest or any pytest-related dependencies are missing from the project, use uv to add them
