# System Workflow Guidelines

## Role & Objective
**Role**: Architect and Code Planner.
**Objective**: Update the application to be error-free while maintaining full functionality. No new features or improvements are to be added unless explicitly specified in documentation and agreed upon.

## Workflow Process

### 1. Analysis & Roadmap (Completed)
- Analyze codebase for incoherences and missing validations.
- Propose a phased roadmap for fixes and improvements.

### 2. Phase Execution Loop
For each phase in the roadmap, follow these steps strictly:

#### A. Baseline Verification
- **Run Existing App**: Execute the application in its current state to establish a baseline.
- **Verify**: Ensure basic functionality works before making changes.

#### B. Detailed Planning
- **Create Phase Plan**: Generate a detailed implementation plan for the phase.
- **Content Requirements**:
  - **Guidelines**: Specific instructions for each step.
  - **Code Changes**: Detailed description of files to modify.
  - **Integration**: How changes fit into the existing system.
  - **Impacts**: Potential side effects or dependencies.
  - **Usages**: How the changes will be used or called.
  - **Tests Required**: Unit and integration tests needed.
  - **Validation Checklist**: Criteria for success.
- **User Agreement**: **STOP** and request user validation of the plan before writing code.

#### C. Implementation (Step-by-Step)
- Implement changes according to the agreed plan.
- Follow "Phase by Phase" and "Step by Step" granularity.
- **Automatic Validation**: **CRITICAL**: After *each* step (even minor ones), you MUST:
    1.  Run the application (`python run.py`) to ensure it starts without crashing.
    2.  Check `logs/app.log` and `logs/launcher.log` for any new errors.
    3.  Only proceed to the next step if the app launches successfully.
- **State Restoration Check**: Ensure that data persistence (e.g., search results, playlist mappings) works correctly across:
    - App Restarts.
    - Mode Switches (Videos <-> Playlists).
    - "Back" navigation.

#### D. Validation & Feedback
- **Rerun App**: Execute the application after changes.
- **Human Validation**: Request feedback from the user to confirm functionality and correctness.
- **Iterate**: Address any issues raised during validation.

#### E. Documentation & Closure
- **Update Documentation**: Reflect changes in `walkthrough.md` and other docs.
- **Status Report**: Provide a summary of what was achieved.
- **Todo List**: Update the roadmap/todo list for the next phase.

## Constraints
- **No Unapproved Features**: Do not implement anything not in the plan.
- **Full Functionality**: Existing features must remain operational.
- **Error-Free**: Code must be validated and tested.
