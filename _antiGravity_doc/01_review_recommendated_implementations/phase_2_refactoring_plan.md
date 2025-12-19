# Phase 2: Refactoring for Testability & Maintenance

## Goal
Refactor the monolithic `src/pages/main/main_page.py` (3500+ lines) into smaller, focused components. This will improve maintainability, testability, and help isolate bugs like the "Back to Results" persistence issue.

## Strategy
We will extract distinct responsibilities from `MainPage` into separate controller/handler classes. `MainPage` will act as a facade/coordinator.

## Steps

## Steps

### Step 2.1: Extract State Management (Completed)
- [x] Create `src/state_manager.py` for centralized state persistence.
- [x] Integrate `StateManager` into `main_page.py`.

### Step 2.2: Create Handler Modules
- [ ] Create `src/pages/main/handlers/` directory.
- [ ] **Create `VideoUIHandler`** (`src/pages/main/handlers/video_ui_handler.py`):
    - Move video tree rendering, row formatting, and highlighting logic here.
    - Move `populate_videos_table_preview` here (and ensure it doesn't save state).
- [ ] **Create `PlaylistUIHandler`** (`src/pages/main/handlers/playlist_ui_handler.py`):
    - Move playlist tree rendering, search execution, and mapping logic here.
- [ ] **Create `ActionHandler`** (`src/pages/main/handlers/action_handler.py`):
    - Move "Back to Results", exports, and navigation logic here.
    - This handler will coordinate between `VideoUIHandler` and `StateManager`.

### Step 2.3: Refactor MainPage as Facade
- [ ] Update `src/pages/main/main_page.py` to:
    - Initialize `VideoUIHandler`, `PlaylistUIHandler`, and `ActionHandler`.
    - Delegate events to these handlers.
    - Remove the bulk of the logic, keeping only initialization and layout wiring.

### Step 2.4: Verify & Fix "Back to Results"
- [ ] Verify that `ActionHandler.back_to_video_results` correctly calls `StateManager.load` and `VideoUIHandler.render`.
- [ ] Verify that `VideoUIHandler.populate_preview` does *not* trigger any state saving.

## Validation
- **Automatic**: App must launch after each extraction.
- **Manual**: Verify "Back to Results" works after Step 2.4.
