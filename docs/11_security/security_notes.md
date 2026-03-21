# Security Notes

## Security Baseline

- API keys must be provided via environment variables.
- No hardcoded secrets in committed source.
- Cloud inference (Cerebras) is allowed by design.
- No formal compliance regime currently required (student project context).

## Current Risks

- Potential accidental secret leakage in local helper files or scripts.
- No formal RBAC or auth layer around internal tool endpoints.
- Mixed client surfaces (Unity/mobile/web/ESP) increase attack surface.
- BLE and LAN channels need clear trust boundaries and sanitization.

## Recommended Controls

- Add secrets scanning in CI/pre-commit.
- Add endpoint authentication for non-local deployments.
- Add request validation and rate limiting for high-risk routes.
- Add explicit CORS origin restrictions for production.
- Define data retention policy for audio and telemetry artifacts.

