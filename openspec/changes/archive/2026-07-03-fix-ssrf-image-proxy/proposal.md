# Proposal: Fix SSRF in Image Proxy

## Problem
The `/api/proxy/image` endpoint in `system.py` accepts any URL and makes a server-side request to fetch it. This is a Server-Side Request Forgery (SSRF) vulnerability. An attacker can use this endpoint to scan internal networks, access cloud metadata services, or bypass IP restrictions.

## Proposed Solution
Implement a strict domain whitelist and protocol validation for the image proxy endpoint. Only allow `http` and `https` protocols, and restrict requests to known podcast and media platforms.

## Goals
- Prevent SSRF attacks via the image proxy.
- Ensure legitimate podcast cover images and external media continue to load.

## Non-Goals
- We are not implementing an outbound proxy for all requests.
- We are not implementing an image resizing or caching service.
