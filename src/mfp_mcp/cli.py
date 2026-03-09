"""CLI commands for MyFitnessPal MCP Server."""

import sys

from mfp_mcp.auth import (
    AuthStatus,
    clear_credential,
    get_credential,
    get_storage_backend,
    is_keyring_available,
    store_credential,
    validate_auth_sync,
)
from mfp_mcp.auth.browser import extract_mfp_cookies


def cmd_auth(from_browser: str | None = None) -> int:
    """Interactive authentication flow."""
    print("MyFitnessPal MCP Authentication")
    print("=" * 40)
    print()

    if not is_keyring_available():
        print("Warning: No system keyring available.")
        print("Cookies will be stored in an encrypted file.")
        print()

    # Check for existing credential
    existing = get_credential()
    if existing.success and existing.cookies:
        print("Existing credential found. Validating...")
        result = validate_auth_sync(existing.cookies)
        if result.is_valid:
            print(f"Already authenticated as: {result.username}")
            print()
            if not from_browser:
                response = input("Re-authenticate? [y/N]: ").strip().lower()
                if response != "y":
                    return 0

    # Get cookies from browser or manual input
    if from_browser:
        print(f"Extracting cookies from {from_browser}...")
        browser_result = extract_mfp_cookies(from_browser if from_browser != "auto" else None)
        if not browser_result.success:
            print(f"Error: {browser_result.message}")
            return 1
        cookies = browser_result.cookies
        print(f"Found cookies in {browser_result.browser}")
    else:
        print()
        print("To authenticate, extract cookies from your browser automatically:")
        print()
        print("  mfp-mcp auth --from-browser chrome")
        print("  mfp-mcp auth --from-browser auto    # try all browsers")
        print()
        print("Make sure you're logged into www.myfitnesspal.com first.")
        print()
        return 1

    print()
    print("Validating...")

    result = validate_auth_sync(cookies)

    if not result.is_valid:
        print(f"Error: {result.message}")
        if result.status == AuthStatus.EXPIRED:
            print("The cookies may have expired. Log in again and retry.")
        elif result.status == AuthStatus.INVALID:
            print("The cookies appear to be invalid.")
        return 1

    store_result = store_credential(cookies)
    if not store_result.success:
        print(f"Error storing credential: {store_result.message}")
        return 1

    print()
    print("Authentication successful!")
    if result.username:
        print(f"  Username: {result.username}")
    print()
    print("You can now use 'mfp-mcp serve' to start the MCP server.")

    return 0


def cmd_auth_status() -> int:
    """Check current authentication status."""
    cred = get_credential()
    if not cred.success or not cred.cookies:
        print("Not authenticated.")
        print("Run 'mfp-mcp auth --from-browser auto' to authenticate.")
        return 1

    print("Checking authentication status...")
    result = validate_auth_sync(cred.cookies)

    if result.is_valid:
        print("Authenticated")
        if result.username:
            print(f"  Username: {result.username}")
        print(f"  Storage: {get_storage_backend()}")
        return 0
    else:
        print(f"Authentication invalid: {result.message}")
        print("Run 'mfp-mcp auth --from-browser auto' to re-authenticate.")
        return 1


def cmd_auth_clear() -> int:
    """Clear stored credentials."""
    result = clear_credential()
    if result.success:
        print("Credentials cleared.")
    else:
        print(f"Note: {result.message}")
    return 0


def cmd_serve() -> int:
    """Start the MCP server."""
    from mfp_mcp.server import run_server

    return run_server()


def cmd_config() -> int:
    """Output Claude Code MCP config snippet."""
    import json
    import shutil
    from pathlib import Path

    mfp_mcp_path = shutil.which("mfp-mcp")
    if not mfp_mcp_path:
        mfp_mcp_path = str(Path(sys.executable).parent / "mfp-mcp")

    config = {
        "myfitnesspal": {
            "command": mfp_mcp_path,
            "args": ["serve"]
        }
    }

    print('Add this to your Claude Code config inside "mcpServers": {}')
    print()
    print(json.dumps(config, indent=2))
    return 0


def cmd_help() -> int:
    """Show help message."""
    print("MyFitnessPal MCP Server")
    print()
    print("Usage: mfp-mcp <command> [options]")
    print()
    print("Commands:")
    print("  auth                  Authenticate with MyFitnessPal")
    print("    --from-browser X    Extract cookies from browser (chrome, firefox, safari, edge, auto)")
    print("  auth-status           Check authentication status")
    print("  auth-clear            Clear stored cookies")
    print("  config                Output Claude Code MCP config snippet")
    print("  serve                 Start the MCP server")
    print("  help                  Show this help message")
    print()
    print("Examples:")
    print("  mfp-mcp auth --from-browser auto     # Auto-detect browser")
    print("  mfp-mcp auth --from-browser chrome")
    print("  mfp-mcp auth-status")
    print("  mfp-mcp serve")
    print()
    return 0


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        return cmd_help()

    command = sys.argv[1].lower()

    if command == "auth":
        from_browser = None
        args = sys.argv[2:]
        if "--from-browser" in args:
            idx = args.index("--from-browser")
            if idx + 1 < len(args):
                from_browser = args[idx + 1]
            else:
                print("Error: --from-browser requires a browser name (chrome, firefox, auto, etc.)")
                return 1
        return cmd_auth(from_browser=from_browser)

    commands = {
        "auth-status": cmd_auth_status,
        "auth-clear": cmd_auth_clear,
        "config": cmd_config,
        "serve": cmd_serve,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
    }

    if command in commands:
        return commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Run 'mfp-mcp help' for usage.")
        return 1
