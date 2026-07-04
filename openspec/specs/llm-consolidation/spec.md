# llm-consolidation Specification

## Purpose
TBD - created by archiving change consolidate-llm-calls. Update Purpose after archive.
## Requirements
### Requirement: Unified LLM Error Handling
The `call_llm` utility MUST NOT raise web-framework specific exceptions (like `HTTPException`) and instead raise a custom standard `Exception` such as `LLMError`.

#### Scenario: Network Failure
- Given the system attempts to call the LLM and the network request times out
- When `call_llm` catches the connection error
- Then it raises an `LLMError` instead of a FastAPI `HTTPException`.

### Requirement: Network Proxy Fallback
The `call_llm` utility MUST implement a two-tier fallback strategy (Proxy -> Direct DoH) to ensure high availability under complex network environments.

#### Scenario: Proxy Success
- Given the user has a system proxy configured
- When `call_llm` initiates a request
- Then it first attempts the request with `trust_env=True` and succeeds without triggering DoH.

#### Scenario: Proxy Failure
- Given the user's proxy rejects the LLM endpoint connection
- When the first `trust_env=True` request fails
- Then it falls back to `trust_env=False` wrapped in `doh_dns_bypass` and retries the request.

