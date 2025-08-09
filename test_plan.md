# CaliBOT Refactoring Test Plan

This document outlines the testing strategy to validate the fixes and refactoring changes proposed in `immediate_changes.md`.

### **Phase 1: Pre-Refactoring Baseline**

**Objective:** Ensure all existing tests pass before any changes are made. This confirms that any failures post-refactoring are due to the new code.

1.  **Run Full Test Suite:**
    ```bash
    python tests/test_all_fixes.py
    ```
2.  **Manual Smoke Test:**
    -   Perform a basic "create event" and "query event" operation to ensure the live bot is responsive.

### **Phase 2: Testing for "Last N" Events (Change #1)**

**Objective:** Verify that the bot correctly interprets and acts on commands like "delete the last 2 events."

1.  **Create a New Test File:** `tests/test_relative_quantifiers.py`
2.  **Test Scenarios:**
    -   Create 4-5 events for a single day.
    -   Send a command: "delete the last 2 events."
        -   **Expected:** The bot should identify the correct two events and ask for confirmation.
    -   Send a command: "move the first lesson to tomorrow."
        -   **Expected:** The bot should correctly identify the earliest lesson and ask for confirmation.
    -   Send a command: "cancel the last event."
        -   **Expected:** The bot should identify the latest event and ask for confirmation.

### **Phase 3: Testing the One-by-One Confirmation Flow (Change #2)**

**Objective:** Ensure the one-by-one confirmation flow is robust and handles "yes," "no," and "cancel" correctly.

1.  **Create a New Test File:** `tests/test_one_by_one_flow.py`
2.  **Test Scenarios:**
    -   Identify 3-4 events for a multi-event operation (e.g., "delete all lessons today").
    -   Choose the "one by one" option.
    -   For the first event, respond "no" (or click the "No" button).
        -   **Expected:** The bot should immediately present the *second* event for review without exiting the flow.
    -   For the second event, respond "yes."
        -   **Expected:** The bot should confirm the action for the second event and then present the *third* event.
    -   For the third event, respond "cancel."
        -   **Expected:** The bot should confirm the cancellation of the remaining operations and exit the flow gracefully.

### **Phase 4: Testing the Redundant Confirmation Loop (Change #3)**

**Objective:** Verify that a new command correctly cancels any pending multi-event operation.

1.  **Create a New Test File:** `tests/test_confirmation_interruption.py`
2.  **Test Scenarios:**
    -   Initiate a multi-event operation (e.g., "update all my meetings").
    -   The bot should present the confirmation message with "All," "One by one," etc.
    -   **Do not respond.** Instead, send a completely new command, like "what's on my calendar for tomorrow?"
        -   **Expected:** The bot should *not* re-prompt for the old confirmation. It should cancel the pending operation and immediately process the new query for tomorrow's events.

### **Phase 5: UI/UX and Inline Keyboard Testing (Change #4)**

**Objective:** Ensure all user confirmations use single-row inline keyboards and that text-based confirmations are no longer prompted.

1.  **Manual UI Review:** This is primarily a manual test.
2.  **Test Scenarios:**
    -   Trigger every confirmation flow in the application:
        -   Multi-event delete/update.
        -   Single event delete/update.
        -   Duplicate event creation.
    -   **Expected:**
        -   Every confirmation prompt MUST appear with inline buttons.
        -   All buttons for a single prompt MUST be in the same row.
        -   The bot should NEVER ask the user to type "yes," "no," "cancel," etc.
        -   Clicking the buttons should trigger the correct actions.

### **Phase 6: Post-Refactoring Validation (Change #5)**

**Objective:** Ensure that after all the refactoring (service consolidation, UI helper deprecation), the bot's functionality remains intact.

1.  **Run Full Test Suite Again:**
    ```bash
    python tests/test_all_fixes.py
    ```
    -   **Expected:** All tests should pass. Any failures must be investigated as regressions.
2.  **Run New Test Files:**
    -   Execute the new test files created in Phases 2, 3, and 4.
    -   **Expected:** All new tests should pass, confirming the specific bug fixes.
3.  **Final Manual Smoke Test:**
    -   Perform a comprehensive set of manual tests covering all core intents: `create`, `update`, `delete`, `query`, and `batch_create`.
    -   Verify that the user experience is consistent and adheres to all rules in `BOT_RULES.md`.
