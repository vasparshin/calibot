# CaliBOT Bug Log

## Purpose
Track specific bugs reported by user testing. Bugs are only marked as FIXED after explicit user confirmation.

## Bug Status Legend
- 🔴 **ACTIVE** - Bug confirmed and needs fixing
- 🟡 **IN PROGRESS** - Fix attempted, awaiting user verification  
- 🟢 **FIXED** - User confirmed bug is resolved
- 🔵 **LOW PRIORITY** - Known issue, not critical

---

## v0.1.220 - Current Version Testing

### 🔴 **ACTIVE BUGS**

#### **BUG-027: Event Name Capitalization Issues** - 🔴 **CRITICAL**
- **Description**: Event names not preserving Google Calendar format or auto-capitalizing properly
- **Evidence**: Inconsistent capitalization between Google Calendar and CaliBOT
- **Expected**: Preserve Google Calendar format, auto-capitalize user input appropriately
- **Impact**: Inconsistent event naming
- **Status**: 🔴 **ACTIVE** - Needs capitalization logic

#### **BUG-028: Hyperlink Formatting Still Broken** - 🔴 **CRITICAL**
- **Description**: Hyperlinks showing as visible text instead of clickable links
- **Evidence**: `[Test Meeting](https://calendar.google.com/calendar/event?eid=...)` showing as text
- **Impact**: Users see raw URLs instead of clickable links
- **Status**: 🔴 **ACTIVE** - Needs hyperlink rendering fix

---

## Bug Tracking Rules

1. **Only mark bugs as FIXED after explicit user confirmation**
2. **Track all attempted fixes in changelog references**
3. **Include user's exact description of the bug**
4. **Update status based on user feedback only**
5. **Maintain historical record of all attempts**
