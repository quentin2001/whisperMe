# Specifications: Image Proxy SSRF Fix

## Requirements

1. **Protocol Validation**: The requested URL must strictly start with `http://` or `https://`.
2. **Domain Whitelist**: The URL hostname must exactly match or be a subdomain of the following allowed domains:
   - `xiaoyuzhoufm.com`
   - `bilibili.com`
   - `hdslb.com`
   - `xmcdn.com`
   - `lizhi.fm`
   - `music.126.net`
   - `126.net`
3. **Error Handling**: If validation fails, the API must return an HTTP 403 Forbidden error with a clear message indicating the domain is not allowed.
4. **Resilience**: The existing image format validation (e.g., checking `Content-Type`) must remain intact.
