# Design: Consolidate LLM Calls

## Architecture Changes

### Unified `llm_utils.py`
1. Define a custom exception `LLMError(Exception)`.
2. Refactor `call_llm` to include the double-fallback mechanism:
   - Tier 1: `httpx.Client(trust_env=True)`
   - Tier 2: `httpx.Client(trust_env=False)` wrapped in `doh_dns_bypass(api_url)`
3. Handle API configurations (URL, token, model) directly inside `call_llm` using `config.py`.
4. Replace `raise HTTPException(...)` with `raise LLMError(...)`.

### Refactoring Consumers
- **`speaker.py`**: Remove `_call_llm_api`. Use `call_llm`. Catch `LLMError` and return `""` to preserve its original fallback behavior.
- **`transcriber.py`**: Remove `_call_llm`. Use `call_llm`. Let `LLMError` propagate.
- **`summarizer.py`**: Remove `_call_llm`. Use `call_llm(..., timeout=600.0)`.

## Testing Strategy
- Create a test script (`tests/test_llm_utils.py`) that uses `unittest.mock.patch` to mock `httpx.Client.post`.
- Test scenarios for successful proxy response, proxy failure leading to DoH fallback success, and total failure.
- Ensure `$env:NO_PROXY="localhost,127.0.0.1"` is applied during script execution to avoid proxy interception of localhost.
