# minor-fixes Specification

## Purpose
TBD - created by archiving change phase1-minor-fixes. Update Purpose after archive.
## Requirements
### Requirement: Prevent React TDZ Crashes
The frontend codebase MUST NOT rely on block-scoped constants declared after their closure usage, avoiding Temporal Dead Zone crashes.

#### Scenario: User visits settings page
- Given a user navigates to the settings view
- When the React component renders and invokes hooks or event handlers
- Then the page must render successfully without throwing `ReferenceError: Cannot access 'API' before initialization`.

### Requirement: Magic Number Elimination
The backend subprocess execution flags MUST use official Python constants rather than hardcoded hex values.

#### Scenario: Backend subprocess creation
- Given the system attempts to run a background ffmpeg command on Windows
- When the subprocess is spawned
- Then it uses `subprocess.CREATE_NO_WINDOW` explicitly.

