# Proposal: Consolidate LLM Network Calls

## Problem
Currently, there are four separate implementations of LLM HTTP calling logic scattered across `llm_utils.py`, `speaker.py`, `transcriber.py`, and `summarizer.py`.
They have inconsistent fallback strategies, error handling (e.g., throwing FastAPI's `HTTPException` inside background tasks), and timeout logic. This makes maintenance and testing extremely difficult.

## Proposed Solution
Unify all LLM calls into `llm_utils.py`. The unified method will implement a robust two-tier network strategy: 
1. Try the system proxy (`trust_env=True`).
2. Fallback to direct DoH DNS bypass (`trust_env=False`).
All callers (`speaker.py`, `transcriber.py`, `summarizer.py`) will be updated to import and use this single `call_llm` function.

## Goals
- Remove duplicated code.
- Provide a consistent, robust proxy/DoH fallback mechanism for all LLM calls.
- Standardize error handling without polluting core modules with FastAPI-specific exceptions.

## Non-Goals
- We are not changing the business logic of prompts or LLM processing.
