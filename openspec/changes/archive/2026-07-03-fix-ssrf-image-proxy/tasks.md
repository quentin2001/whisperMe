# Tasks: Fix SSRF in Image Proxy

- [x] Task 1: Update `backend/app/routers/system.py` to import `urllib.parse`.
- [x] Task 2: Define `ALLOWED_IMAGE_DOMAINS` set in `system.py` with the required platforms.
- [x] Task 3: Refactor the `proxy_image` route to parse the URL and validate the scheme and hostname against the whitelist.
- [x] Task 4: Change error responses in `proxy_image` to use `HTTPException(status_code=403)`.
- [x] Task 5: Start the backend server locally and verify that a valid URL succeeds.
- [x] Task 6: Verify that an invalid URL (e.g., `http://127.0.0.1:9101/`) is rejected with a 403 Forbidden.
