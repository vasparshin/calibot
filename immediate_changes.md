## Immediate Changes for Calibot

### 1. **NLP Intent Extraction for "Last N" Events**

**Problem:** The bot incorrectly interprets relative quantifiers like "last two," leading to the wrong events being selected for an operation.

**Solution:** The system prompt for the NLP agent needs to be updated to handle these cases more accurately. The model should be instructed to include a `limit` and `order` in its JSON output when it detects such phrases. The calendar service must then be updated to use these parameters.

**Files to Modify:**
1.  `backend/app/agent/nlp_agent.py`
2.  `backend/app/services/google_calendar.py`

**Change Description:**
- In `nlp_agent.py`:
    - Add instructions to the system prompt to recognize phrases like "last X," "first X," "next X."
    - Specify that the model should output `limit: X` and `order: "desc"` (for "last") or `order: "asc"` (for "first"/"next").
- In `google_calendar.py`:
    - Update the `query_events` method to accept `limit` and `order` parameters.
    - If these parameters are present, use them to sort the events and limit the results *after* fetching them from the Google Calendar API.

---

### 2. **Broken One-by-One Confirmation Flow**

**Problem:** In the one-by-one confirmation process, if the user replies "no" to an event, the bot either gets stuck, exits the flow, or re-displays the same confirmation message instead of moving to the next event.

**Solution:** The logic for handling user responses during the one-by-one confirmation needs to be fixed in the active event queue handler.

**Files to Modify:**
1.  `backend/app/services/event_queue_handler.py`: This is the active handler for these operations. It needs a method to correctly skip an event and proceed.
2.  `backend/app/api/routes.py`: The webhook handler needs to correctly process the 'no' response by calling the new skip method.

**Change Description:**
- In `event_queue_handler.py`:
    - Implement a `skip_event_and_get_next(chat_id)` method. This method should:
        1.  Remove the current event from the head of the user's pending queue.
        2.  Return the *next* event for review, or `None` if the queue is empty.
- In `routes.py`:
    - Within the `process_user_message` or a dedicated callback handler, when the user input is 'n' or 'no' (or the corresponding callback data), call `event_queue_handler.skip_event_and_get_next(chat_id)`.
    - If the method returns a new event, display it for review using the standard confirmation format.
    - If the method returns `None`, send a message confirming the completion of the operation.

---

### 3. **Redundant Confirmation Loop**

**Problem:** The bot gets stuck in a confirmation loop, repeatedly asking for confirmation for the same set of events, even when the user provides new, unrelated instructions.

**Solution:** The bot's state management needs to be improved. When a new command is received while a multi-event operation is pending, the old operation must be cleared to prevent confusion.

**File to Modify:** `backend/app/api/routes.py`

**Change Description:**
- At the beginning of the `process_user_message` function, before intent extraction, add a check:
    - `is_new_command = not is_confirmation_response(user_message)`
    - If `is_new_command` is true and `event_queue_handler.has_pending_queue(chat_id)` is also true, then:
        - Call `event_queue_handler.clear_pending_queue(chat_id)`.
        - Optionally, send a message to the user like "Cancelling previous operation and starting fresh."
- This ensures that any new request from the user clears out any old, pending confirmations.

---

### 4. **CRITICAL: Event Display Format Consistency**

**Problem:** User asking the same question ("what's scheduled today", "what events are on my calendar today", "what's on the schedule for today") get different response formats. The query intent handler uses AI service for formatting instead of MessageFormatter, resulting in inconsistent event displays that don't follow BOT_RULES.md specifications.

**Solution:** ALL event displays (query, create, update, delete confirmations) MUST use MessageFormatter.format_single_event_display() and follow the exact BOT_RULES.md format: `• [Event Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)`

**Files to Modify:**
1. `backend/app/api/routes.py`: Fix query intent handler (lines 875-902) to use MessageFormatter instead of AI service
2. `backend/app/services/ai_service.py`: Remove event formatting responsibility from AI service
3. `backend/app/prompts/agent_system_prompt.py`: Update to focus on conversation, not formatting

**Change Description:**
- In `routes.py` query intent handler:
    - Replace AI service formatting with direct MessageFormatter usage
    - For single event: Use MessageFormatter.format_single_event_display()
    - For multiple events: Use MessageFormatter.format_event_list_display() 
    - Add consistent title: "Today's schedule includes:" or "Found X events:"
    - Ensure ALL event displays include hyperlinks, full dates, times, and calendar names
- In `ai_service.py`:
    - Remove event formatting logic - AI should only handle conversational responses
    - Focus on small talk and confirmation guidance only
- In `agent_system_prompt.py`:
    - Remove formatting instructions - events should be pre-formatted before AI processing

---

### 5. **UI/UX Consistency and Interactive Buttons**

**Problem:** The bot's responses are inconsistent. Some use plain text for confirmations, while others use keyboards. This leads to a confusing user experience. Buttons are not used consistently, and when they are, they are not in a single row.

**Solution:** All user-facing messages requiring a choice or confirmation MUST use inline keyboards (buttons). This provides a cleaner and more intuitive interface. Text-based confirmations should be deprecated.

**Files to Modify:**
1.  `backend/app/services/telegram.py`: Centralize and standardize the creation of inline keyboards.
2.  `backend/app/api/routes.py`: Update all confirmation flows to use the new standardized inline keyboard functionality.
3.  `BOT_RULES.md`: Update the rules to reflect the mandatory use of single-row inline keyboards.

**Change Description:**
- In `telegram.py`:
    - Modify the `create_confirmation_keyboard` function. It should accept a list of button configurations (text and callback data).
    - Ensure the function generates a keyboard with all buttons in a **single row** as per the new rule.
- In `routes.py`:
    - Replace all `send_message` calls that ask for a typed response (like 'yes'/'no'/'all') with calls that use a `reply_markup` generated by the updated `create_confirmation_keyboard`.
    - Example button setup for multi-event confirmation: `[["✅ Yes, All", "✍️ One by One", "❌ Cancel"]]`.
    - The callback data for each button must be a unique identifier that the webhook can process (e.g., `confirm_all_{op_id}`, `confirm_one_{op_id}`).
- In `BOT_RULES.md`:
    - Add a new section: "**Mandatory Inline Keyboard Usage**".
    - Mandate that all questions to the user MUST be presented with inline keyboard options.
    - Specify that buttons should be arranged in a single row for consistency.
    - Prohibit asking the user to type out confirmation words. The only accepted user input should be via button clicks.

---

### 5. **Code Optimization and Refactoring Opportunities**

After a comprehensive review of the backend code, several opportunities for optimization and refactoring have been identified. These changes will reduce code duplication, improve maintainability, and align the codebase with best practices.

#### a. **Consolidate NLP and AI Services**

**Problem:** The `ai_service.py` and `nlp_agent.py` have overlapping responsibilities. `nlp_agent.py` is responsible for structured intent extraction, while `ai_service.py` handles conversational responses. This separation is logical, but the two can be merged into a single, more powerful `AIService` to streamline LLM interactions.

**Solution:** Merge `nlp_agent.py` into `ai_service.py`.

**Files to Modify:**
1.  `backend/app/services/ai_service.py`: Absorb the methods from `nlp_agent.py`.
2.  `backend/app/api/routes.py`: Update all calls from `nlp_agent` to the new methods in `ai_service`.

**Change Description:**
- Move `check_relevancy` and `extract_intent` from `nlp_agent.py` to `ai_service.py`.
- The new `AIService` will handle all interactions with the LLM, including relevancy checks, intent extraction, and generating conversational responses.
- This consolidation will reduce the number of service instances that need to be managed in `routes.py`.

#### b. **Centralize and Simplify UI Formatting**

**Problem:** The `ui_helpers.py` file contains a mix of legacy and new formatting functions, leading to confusion and inconsistent UI. The `message_formatter.py` and `inline_keyboard.py` files were introduced to solve this, but the old helpers are still in use.

**Solution:** Deprecate `ui_helpers.py` and move all essential formatting logic into `message_formatter.py` and `inline_keyboard.py`.

**Files to Modify:**
1.  `backend/app/utils/message_formatter.py`: Ensure it contains all necessary text formatting functions.
2.  `backend/app/utils/inline_keyboard.py`: Ensure it handles all keyboard generation.
3.  `backend/app/api/routes.py`: Refactor to exclusively use the new centralized formatters.
4.  `backend/app/utils/ui_helpers.py`: Mark as deprecated and remove unused functions.

**Change Description:**
- Move functions like `format_event_for_display` and `get_calendar_display_name` into `message_formatter.py`.
- Ensure all keyboard generation logic is in `inline_keyboard.py`.
- Refactor `routes.py` to remove all dependencies on `ui_helpers.py`.

#### c. **Streamline `routes.py` Logic**

**Problem:** The main `routes.py` file has become overly complex, handling too many distinct states and logic flows directly within the `process_user_message` function. This makes it difficult to debug and maintain.

**Solution:** Refactor `routes.py` by delegating more logic to the respective service handlers.

**Files to Modify:**
1.  `backend/app/api/routes.py`: Simplify the main webhook handler.
2.  `backend/app/services/event_queue_handler.py`: This handler should manage its own state more independently.

**Change Description:**
- In `routes.py`, the `process_user_message` function should be a high-level orchestrator. Its primary job is to:
    1.  Check for pending operations.
    2.  Extract intent using the `AIService`.
    3.  Route the intent to the appropriate handler (`event_queue_handler`, `calendar_service`, etc.).
- Move complex stateful logic, like duplicate checks and multi-step confirmations, into the `event_queue_handler`. For example, the handler should manage the confirmation flow for duplicates internally, rather than setting flags that `routes.py` has to check on the next request.
- This will make `routes.py` cleaner and more focused on routing, while the service handlers manage their own logic.

#### d. **Unify Multi-Event Handling (Deprecate multi_event_operations.py)**

**Problem:** Duplicate logic between `event_queue_handler.py` and `multi_event_operations.py` causes state drift and excess LOC.

**Action:** Migrate required features (batch delete/update confirmation, per-event change summaries) into `EventQueueHandler`; remove references to `MultiEventOperationHandler` in `routes.py`; delete legacy file after migration.

**Success Criteria:** No imports of `multi_event_operations` remain; all multi-event flows pass existing and new tests.

#### e. **Deprecate Legacy UI Helpers**

**Problem:** `ui_helpers.py` duplicates formatting now centralized in `message_formatter.py` & `inline_keyboard.py`.

**Action:** Move any unique functions (if still needed) to `message_formatter.py`; add deprecation shim or remove file; update imports.

**Success Criteria:** Grep shows no usages of `ui_helpers.`; all confirmation / success messages still conform to BOT_RULES.

#### f. **Merge NLPAgent into AIService**

**Problem:** Two LLM layers (`nlp_agent.py`, `ai_service.py`) increase complexity.

**Action:** Create unified `AIService` with: `check_relevancy`, `extract_intent`, `generate_small_talk_response`, `generate_agent_response`.

**Success Criteria:** `nlp_agent.py` removed; routes instantiate single service; tests for intent extraction & relevancy still pass.

#### g. **Intent Dispatch Registry**

**Problem:** Monolithic `process_user_message` branching obscures flow.

**Action:** Introduce dispatcher mapping intent -> handler function (create/update/delete/query/calendar_management/batch_create). Each handler returns structured result (messages, keyboards, state ops).

**Success Criteria:** `process_user_message` < 150 LOC and purely orchestrates pipeline (auth -> relevancy -> intent -> dispatch -> respond).

#### h. **Standard Event Action Model**

**Problem:** Repeated dictionary key checks for events.

**Action:** Introduce Pydantic `EventActionRequest` (fields: intent, event_name, date, start_time, end_time, calendar_id, update fields, limit, order). Normalize LLM output before handlers.

**Success Criteria:** Removal of repetitive `if 'intent' not in event_data` and defensive type checks; handlers accept validated objects.

#### i. **Batch Creation & Duplicate Flow Consolidation**

**Problem:** Multiple batch parsing paths (arrays, description parsing) and duplicate handling repeated.

**Action:** Implement `normalize_batch_events(event_data)` + `create_batch(events)` utility with optional duplicate filter returning (created, duplicates, failures). Single response formatter builds final message + duplicate confirmation prompt.

**Success Criteria:** Only one code path for batch creation; duplicate confirmation logic isolated; reduced LOC in routes.

---

### Implementation Order (Risk Mitigation)
1. Add limit/order to `google_calendar.query_events` + tests.
2. Add EventActionRequest model + adapter layer (non-breaking).
3. Merge NLP into AIService (keep transitional wrapper if needed).
4. Introduce dispatcher and refactor routes.
5. Unify multi-event handling & remove legacy handler.
6. Consolidate UI formatting & remove ui_helpers.
7. Consolidate batch & duplicate creation logic.
8. Final cleanup (remove deprecated files, adjust imports) & expand tests.

### New / Updated Tests
- `test_intent_limit_order.py`
- `test_queue_unification.py`
- `test_batch_create_duplicates_mixed.py`
- `test_keyboard_uniformity.py`
- `test_referential_pronouns.py`
- `test_event_model_validation.py`

### Metrics for Completion
- No references: `multi_event_operations`, `ui_helpers`, `NLPAgent`.
- process_user_message < 150 LOC.
- All existing + new tests green.
- Message samples still match BOT_RULES (snapshot diff).

---

### 6. **Button Persistence Regression (Must Disappear After Press)**

**Problem:** In recent chat logs, confirmation/status buttons appear to persist across multiple responses (multiple "✅ **Confirmed** - Processing your request..." messages) rather than being removed immediately after the first click. BOT_RULES mandate that inline keyboards be removed (edit_message_text with empty `reply_markup`) after a button is pressed to prevent duplicate actions and clutter.

**Evidence (Excerpt):** Repeated confirmation messages for each updated event instead of a single status then result messages.

**Required Fix:**
1. Audit all callback handlers (`handle_confirmation_callback`, queue progression flows) to ensure every button press performs a single `edit_message_text(..., reply_markup={})` or equivalent keyboard removal.
2. Prevent sending multiple identical "Confirmed" status messages; consolidate into one status + results.

**Files to Modify:**
- `backend/app/api/routes.py`
- `backend/app/services/event_queue_handler.py`
- `backend/app/utils/inline_keyboard.py` (ensure helper enforces ephemeral behavior)

**Acceptance Criteria:**
- No duplicated confirmation status lines per operation.
- Keyboard always removed within the same message upon first click.
- Tests: Add `test_keyboard_ephemeral_regression.py` asserting callback leaves no inline keyboard.

---

### 7. **Calendar Name Display Accuracy**

**Problem:** Displayed calendar name (e.g., `Zoutna`) may not exactly match the Google Calendar API `summary` or expected end‑user friendly name (e.g., should possibly show `Zoutna` vs lowercase email or vice versa). Need deterministic rule: always show the Calendar `summary` as retrieved from API cache, never internal IDs or emails unless rule requires.

**Required Fix:**
1. Centralize calendar name resolution in `MessageFormatter.get_calendar_display_name(calendar_id)` pulling from cached metadata.
2. Replace any direct use of raw `calendar_id` or partial aliases in success & summary messages.

**Files to Modify:**
- `backend/app/utils/message_formatter.py`
- `backend/app/services/google_calendar.py` (ensure cache exposes summary)
- `backend/app/api/routes.py`

**Acceptance Criteria:**
- All event lines use exact calendar `summary` string.
- Add test `test_calendar_name_consistency.py` comparing displayed names vs API metadata.

---

### 8. **Calendar Migration Feedback (Move Between Calendars)**

**Problem:** When user requests moving events to another calendar ("move the lessons to Tonya calendar"), feedback shows multiple interim confirmations and may not clearly state target calendar before execution. Success messages sometimes list original calendar name rather than new destination.

**Required Fix:**
1. In pre-execution summary ("Found X events to update"), explicitly include proposed calendar change: `→ New Calendar: <Target>`.
2. After migration, success message must reflect the new calendar name (not the old) and confirm move action.
3. Ensure underlying update logic actually moves event (modify calendarId via insert+delete or move endpoint if using Google API `events.move`).

**Files to Audit/Modify:**
- `backend/app/api/handlers/update_delete.py`
- `backend/app/services/google_calendar.py` (implement/make sure `move_event` uses `events.move`)
- `backend/app/utils/message_formatter.py`

**Acceptance Criteria:**
- Success messages display destination calendar name.
- Proposed change summary lists calendar transition.
- Add test `test_calendar_migration_display.py` verifying both proposed + final messages.

---

### 9. **One-by-One Flow Message Retention**

**Problem:** Current one-by-one confirmation flow replaces or removes the message containing the event instead of editing it to show decision and then sending a fresh message for the next event. Requirement: keep history clearer by editing the original confirmation message to append the decision (e.g., "Decision: Skipped" / "Decision: Updated") and send a new message for the next pending event.

**Required Fix:**
1. Adjust `event_queue_handler.process_queue_response` (and related callback path) to:
    - Edit current confirmation message: remove buttons, append decision line.
    - Send new confirmation message for next event with fresh keyboard.
2. Provide helper `format_decision_appendix(decision_type, changes)` in `message_formatter.py`.

**Files to Modify:**
- `backend/app/services/event_queue_handler.py`
- `backend/app/utils/message_formatter.py`
- `backend/app/api/routes.py`

**Acceptance Criteria:**
- Each processed event leaves an edited historical message (no buttons) with decision annotation.
- Next event always appears in a brand new message.
- Test `test_one_by_one_message_retention.py` ensures message edit + new message behavior.

---

### 10. **Pre-Execution Proposed Changes Detail**

**Problem:** Summary messages ("Found X events to update (shift by 1 hour)") don't enumerate full proposed transformation per event (new times, new calendar, renames). Requirement: Each event in the pre-execution list must show both CURRENT state and PROPOSED changes.

**Required Fix:**
1. Extend formatter to produce lines like: `• Lesson (link) on Monday ... 09:00 AM - 10:00 AM (Zoutna) → 10:00 AM - 11:00 AM (Tonya)`.
2. If only time shift: show arrow with new times. If calendar change only: arrow with new calendar. If multiple changes: show composite arrow (time + calendar).

**Files to Modify:**
- `backend/app/utils/message_formatter.py`
- `backend/app/api/handlers/update_delete.py`

**Acceptance Criteria:**
- Arrow format consistently used for every proposed change.
- Tests: `test_proposed_change_formatting.py` verifying arrow notation for time shift & calendar move.

---

### 11. **Success Messages Must Reflect Updated State**

**Problem:** Post-update success lines show original times or calendar rather than updated ones (e.g., after +1 hour shift, success still listed original times). User had to query schedule again to see actual changes.

**Required Fix:**
1. Ensure update execution receives updated event payload from Google API response and uses it for success formatting.
2. Formatter must always read start/end/calendar from updated object, not original request object.
3. For time shifts, optionally append a concise change summary (e.g., `(+1h)`).

**Files to Modify:**
- `backend/app/services/google_calendar.py`
- `backend/app/api/handlers/update_delete.py`
- `backend/app/utils/message_formatter.py`

**Acceptance Criteria:**
- Success messages display new times/calendar.
- Added regression test `test_success_message_updated_state.py`.

---

### Implementation Notes for New Issues (6–11)
- Tackle formatting (10 & 11) before migration (8) to reuse enriched formatter.
- Introduce unified `EventChange` dataclass/Pydantic model to pass proposed vs final state for consistent rendering (supports issues 8–11).
- Consolidate keyboard removal & message edit patterns into a single utility to solve issue 6 & support issue 9.

---
