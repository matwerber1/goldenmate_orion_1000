# Project Planning and Tracking Rules

`planning/` directory contains key planning and tracking documents for this project.

## Phase Management (Priority: Critical)

- `project_plan.md` provide general documentation of project design goals, structure, and expectations
- `project_tracking.md` lists implementation steps grouped into phases that must be completed to satisfy project plan requirements
- Whenever you work on something, use `project_tracking.md` to track the status of your work
- If you perform work not listed under a planned phase in the project tracker add it as a single setence list item to "Unplanned work" category
- Maintain alphabetical list of affected Python files per work phase in `project_tracking.md`

## Work status codes (Priority: High)

- **IN_PROGRESS**: When starting a phase or step
- **PENDING_APPROVAL**: When complete with all tests passing
- **APPROVED/SKIPPED**: Only when explicitly instructed
- **Unplanned work**: Record any out-of-scope work as single sentence

## Testing Requirements (Priority: High)

- Add reasonable and lightweight unit tests for all new and modified functionality
- Rerun all new and existing tests and confirm that they are passing before considering your current task complete

## Project plan review (Priority: High)

- Whenever you complete a work phase or make non-trivial or breaking changes, review and update the project plan to match the current strategy in the code base.
