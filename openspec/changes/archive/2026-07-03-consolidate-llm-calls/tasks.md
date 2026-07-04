# Tasks: Consolidate LLM Calls

- [x] Task 1: Refactor `backend/app/core/llm_utils.py` to implement the `LLMError` and double-fallback network strategy.
- [x] Task 2: Remove `_call_llm_api` from `speaker.py` and replace its calls with `llm_utils.call_llm`.
- [x] Task 3: Remove `_call_llm` from `transcriber.py` and replace its calls.
- [x] Task 4: Remove `_call_llm` from `summarizer.py` and replace its calls.
- [x] Task 5: Write unit tests using `unittest.mock` to verify the fallback logic without hitting real endpoints.
- [x] Task 6: Execute tests under PowerShell with `$env:NO_PROXY="localhost,127.0.0.1"`.
