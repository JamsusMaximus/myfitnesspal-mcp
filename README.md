# mfp-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that connects AI assistants to your MyFitnessPal data. Lets Claude read your food diary, nutrition goals, weight measurements, and more.

MFP has no official API - this uses the [myfitnesspal](https://pypi.org/project/myfitnesspal/) Python library which scrapes the website using browser cookies.

## Quick start

```bash
# Install
git clone https://github.com/jevy/myfitnesspal-mcp.git
cd myfitnesspal-mcp
uv sync --extra browser

# Authenticate (must be logged into MFP in your browser first)
mfp-mcp auth --from-browser chrome

# Verify
mfp-mcp auth-status

# Start the server
mfp-mcp serve
```

## Adding to Claude Code

Run `mfp-mcp config` to get the JSON snippet, or add this to your Claude Code project settings (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "myfitnesspal": {
      "command": "/path/to/your/.venv/bin/mfp-mcp",
      "args": ["serve"]
    }
  }
}
```

Replace the path with the output of `which mfp-mcp` after installing.

## Tools

| Tool | Description | Inputs |
|------|-------------|--------|
| `mfp_get_diary` | Get food diary for a single date | `date` (YYYY-MM-DD) |
| `mfp_get_nutrition_summary` | Get nutrition totals across a date range (max 31 days) | `start_date`, `end_date` |
| `mfp_get_goals` | Get calorie and macro goals | none |
| `mfp_get_measurements` | Get body measurements (weight, body fat, etc.) over time | `measurement?`, `start_date?`, `end_date?` |
| `mfp_get_profile` | Get user profile and preferences | none |
| `mfp_search_food` | Search the MFP food database | `query` |
| `mfp_get_food_details` | Get full nutrition for a food item | `mfp_id` |
| `mfp_auth_status` | Check whether authentication is valid | none |
| `mfp_refresh_auth` | Re-extract cookies from browser | `browser?` (auto/chrome/firefox/safari/edge) |

## CLI reference

```
mfp-mcp auth --from-browser <browser>   Authenticate (extract + store cookies)
mfp-mcp auth-status                     Check stored credential validity
mfp-mcp auth-clear                      Remove stored credentials
mfp-mcp config                          Output Claude Code MCP config JSON
mfp-mcp serve                           Start stdio MCP server
mfp-mcp help                            Show help
```

### Authentication

MFP requires browser cookies for access. The `auth` command extracts cookies from your browser and stores them securely.

```bash
# Auto-detect browser
mfp-mcp auth --from-browser auto

# Specific browser
mfp-mcp auth --from-browser chrome
mfp-mcp auth --from-browser firefox
mfp-mcp auth --from-browser safari
```

You must be logged into [myfitnesspal.com](https://www.myfitnesspal.com) in the browser first.

## How authentication works

Credentials are stored using a layered system (checked in order):

1. **Environment variable** (`MFP_COOKIES`) - for CI/testing
2. **System keyring** - macOS Keychain, GNOME Keyring, etc.
3. **Encrypted file** - `~/.config/myfitnesspal-mcp/credentials.enc`

The encrypted file uses AES-256-GCM with a key derived via PBKDF2-HMAC-SHA256 (600,000 iterations) bound to machine-specific identifiers. File permissions are set to 600 (owner-only).

Cookie values are never logged, never included in error messages, and never returned to Claude. Multiple layers of defence prevent accidental leakage:
- `repr=False` on all cookie fields
- Custom `__repr__` implementations that mask values
- Result sanitisation before returning tool responses

## Architecture

```
src/mfp_mcp/
├── cli.py              # CLI entry point
├── server.py           # stdio MCP server, tool registration
├── auth/
│   ├── storage.py      # Unified credential storage (env → keyring → file)
│   ├── keyring.py      # System keyring backend
│   ├── encrypted.py    # AES-256-GCM file backend
│   ├── browser.py      # Browser cookie extraction
│   └── validator.py    # Cookie validation via NextAuth session
├── client/
│   ├── mfp.py          # Async wrapper around myfitnesspal library
│   └── models.py       # Pydantic response models
└── tools/
    ├── _validation.py  # Pydantic input validation
    ├── diary.py        # mfp_get_diary
    ├── nutrition.py    # mfp_get_nutrition_summary
    ├── goals.py        # mfp_get_goals
    ├── measurements.py # mfp_get_measurements
    ├── food.py         # mfp_search_food, mfp_get_food_details
    ├── profile.py      # mfp_get_profile
    ├── auth_status.py  # mfp_auth_status
    └── refresh_auth.py # mfp_refresh_auth
```

## Technical notes

### MFP WAF workaround

The upstream `myfitnesspal` library's `__init__` hits `/user/auth_token` which MFP's WAF now blocks (HTTP 403). This server works around the issue by:

1. Creating the library's `Client` object without calling `__init__` (via `object.__new__()`)
2. Setting up the HTTP session manually with plain `requests` (cloudscraper also gets blocked)
3. Getting the username from MFP's NextAuth session endpoint (`/api/auth/session`)
4. The HTML scraping methods (`get_date`, `get_measurements`) continue to work normally

### Rate limiting

Requests to MFP are throttled to one every 500ms with a lock to prevent concurrent requests. This is conservative to avoid triggering MFP's rate limits.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev --extra browser

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## Requirements

- Python 3.12+
- A MyFitnessPal account with an active browser session
- [uv](https://docs.astral.sh/uv/) for dependency management
