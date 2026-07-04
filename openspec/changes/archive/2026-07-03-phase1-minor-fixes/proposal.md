# Proposal: Phase 1 Minor Fixes

## Problem
Before completing Phase 1, we identified two residual technical debts:
1. **Frontend**: In `SettingsView.jsx`, a `const API` is defined after its usage in the lexical scope of an async function, causing potential TDZ (Temporal Dead Zone) ReferenceErrors under strict rendering conditions or bundlers.
2. **Backend**: Hardcoded magic numbers (`0x08000000`) are scattered across backend subprocess calls for Windows environments, which reduces code readability and maintainability.

## Proposed Solution
- **Frontend**: Hoist the `API` constant declaration to the top of the component or use `API_BASE` directly, ensuring thread-safe access without TDZ.
- **Backend**: Replace all occurrences of `0x08000000` with `subprocess.CREATE_NO_WINDOW` and ensure `subprocess` is correctly imported in those modules (`compat.py`, `ffmpeg.py`, `system.py`).

## Goals
- Eliminate frontend crashes related to variable hosting.
- Clean up backend code by adopting Python standard library constants.
