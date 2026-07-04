# Design: Phase 1 Minor Fixes

## Frontend Adjustments
**File**: `frontend/src/views/SettingsView.jsx`
- Replace local component scope variable `const API = API_BASE;` usage. It is defined at line 93 but referenced inside `handleVerifyHF` around line 79. We will hoist it to the top of the component `SettingsView` (e.g., right after state declarations).
- Testing: After compiling, verify the Settings page loads properly and clicking functions (like Verify HF Token) succeeds without throwing a `ReferenceError` resulting in a white screen.

## Backend Adjustments
- Search for the literal `0x08000000`.
- Expected locations:
  - `backend/app/core/compat.py`
  - `backend/app/core/ffmpeg.py`
  - `backend/app/routers/system.py`
- Action:
  - Replace `0x08000000` with `subprocess.CREATE_NO_WINDOW`.
  - Add `import subprocess` if it is missing from the file.
