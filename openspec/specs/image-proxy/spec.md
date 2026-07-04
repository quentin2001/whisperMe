# image-proxy Specification

## Purpose
TBD - created by archiving change fix-ssrf-image-proxy. Update Purpose after archive.
## Requirements
### Requirement: Validation of URL protocol and domain
The `/api/proxy/image` endpoint MUST restrict requests to explicitly allowed protocols and domains to prevent SSRF.

#### Scenario: Valid whitelisted domain
- Given a proxy request for `https://xiaoyuzhoufm.com/cover.jpg`
- When the `proxy_image` endpoint is called
- Then it validates the scheme is `https` and the domain ends with `.xiaoyuzhoufm.com` or matches exactly, and proxies the image successfully.

#### Scenario: Valid subdomain
- Given a proxy request for `http://i0.hdslb.com/bfs/image.jpg`
- When the `proxy_image` endpoint is called
- Then it validates the domain ends with `.hdslb.com` and proxies the image successfully.

#### Scenario: Invalid external domain
- Given a proxy request for `https://attacker.com/malware`
- When the `proxy_image` endpoint is called
- Then it returns an HTTP 403 Forbidden exception indicating the domain is not allowed.

#### Scenario: Invalid internal domain (SSRF)
- Given a proxy request for `http://127.0.0.1:9101/api/config`
- When the `proxy_image` endpoint is called
- Then it returns an HTTP 403 Forbidden exception.

#### Scenario: Invalid protocol
- Given a proxy request for `file:///etc/passwd`
- When the `proxy_image` endpoint is called
- Then it returns an HTTP 403 Forbidden exception.

