# Design: Image Proxy Whitelist

## Architecture Changes

### Backend (`system.py`)
1. Introduce a constant `ALLOWED_IMAGE_DOMAINS` containing the whitelisted domains.
2. In the `proxy_image` route:
   - Use `urllib.parse.urlparse` to extract the `scheme` and `hostname`.
   - Validate `scheme in ("http", "https")`.
   - Validate the `hostname` against `ALLOWED_IMAGE_DOMAINS`. To support subdomains, use a suffix check (e.g., `hostname == domain or hostname.endswith("." + domain)`).
   - Change the error response from `Response(status_code=400)` to `raise HTTPException(status_code=403, detail="...")`.

## Security Considerations
- The suffix check must include the leading dot (`.`) to prevent bypasses (e.g., `attacker-bilibili.com` should not pass).
- Handling potential `None` hostnames correctly.
