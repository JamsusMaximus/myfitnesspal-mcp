# MFP MCP Server

MyFitnessPal MCP server providing nutrition and measurement data to Claude Code via stdio.

## Project structure

- `src/mfp_mcp/` - Main package
  - `server.py` - MCP server with 9 tool definitions, stdio transport
  - `cli.py` - CLI entry point (`mfp-mcp` command)
  - `auth/` - Layered credential storage (env var → keyring → AES-256-GCM encrypted file)
  - `client/mfp.py` - Async wrapper around sync `myfitnesspal` library, bypasses broken library init
  - `tools/` - One file per tool, Pydantic input validation, standardised error responses
- `tests/` - pytest + pytest-asyncio, mirrors src structure
- `_reference_old/` - Previous FastAPI-based implementation (reference only)

## Key commands

```bash
uv sync --extra browser          # Install with browser cookie support
.venv/bin/pytest                  # Run tests (55 tests)
.venv/bin/mfp-mcp help            # CLI help
.venv/bin/mfp-mcp auth --from-browser chrome  # Authenticate
.venv/bin/mfp-mcp serve           # Start MCP server
```

## Important patterns

- **MFP WAF workaround**: The `myfitnesspal` library's `__init__` is broken (MFP blocks `/user/auth_token` with 403). We bypass it with `object.__new__(Client)` and use the NextAuth session endpoint instead. See `client/mfp.py:_create_mfp_client()`.
- **Cookie security**: Cookie values must NEVER appear in error messages, logs, or tool return values. Use `type(e).__name__` not `str(e)`. All cookie fields use `repr=False`. `refresh_auth.py` sanitises results before returning to Claude.
- **All tools return dicts**: Success returns domain data, errors return `{"isError": True, "error_code": "...", "message": "..."}`.
- **Rate limiting**: 500ms between MFP requests via `MFPClient._throttle()`.
- **Use plain `requests`**: cloudscraper gets blocked by MFP's WAF. Do not switch back.

## Testing

All tests use mocks - no network calls. Run with `pytest` (asyncio_mode=auto configured in pyproject.toml).
