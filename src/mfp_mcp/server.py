"""MCP Server implementation for MyFitnessPal."""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from mfp_mcp.auth import get_credential, validate_auth
from mfp_mcp.tools import (
    mfp_auth_status,
    mfp_get_diary,
    mfp_get_food_details,
    mfp_get_goals,
    mfp_get_measurements,
    mfp_get_nutrition_summary,
    mfp_get_profile,
    mfp_refresh_auth,
    mfp_search_food,
)

# Configure logging to stderr (stdout is used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mfp-mcp")

server = Server("myfitnesspal-mcp")

TOOLS = [
    Tool(
        name="mfp_auth_status",
        description="Check MFP auth status. Use only when other tools return auth errors.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="mfp_refresh_auth",
        description="Refresh auth by extracting cookies from user's browser. Use when other tools return auth errors.",
        inputSchema={
            "type": "object",
            "properties": {
                "browser": {
                    "type": "string",
                    "enum": ["auto", "chrome", "firefox", "safari", "edge"],
                    "description": "Browser to extract from. Use 'auto' to try all.",
                    "default": "auto",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="mfp_get_diary",
        description="Get food diary for a date. Returns meals, entries, totals, goals, water, and notes.",
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "YYYY-MM-DD format.",
                },
            },
            "required": ["date"],
        },
    ),
    Tool(
        name="mfp_get_nutrition_summary",
        description="Get nutrition totals for a date range. Max 31 days. Returns daily totals and averages.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "YYYY-MM-DD. Start of range.",
                },
                "end_date": {
                    "type": "string",
                    "description": "YYYY-MM-DD. End of range.",
                },
            },
            "required": ["start_date", "end_date"],
        },
    ),
    Tool(
        name="mfp_get_goals",
        description="Get the user's nutrition/calorie goals.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="mfp_get_measurements",
        description="Get body measurements (weight, body fat, etc.) over time.",
        inputSchema={
            "type": "object",
            "properties": {
                "measurement": {
                    "type": "string",
                    "description": "Measurement type, e.g. Weight, Body Fat. Default: Weight.",
                    "default": "Weight",
                },
                "start_date": {
                    "type": "string",
                    "description": "YYYY-MM-DD. Optional start date.",
                },
                "end_date": {
                    "type": "string",
                    "description": "YYYY-MM-DD. Optional end date.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="mfp_search_food",
        description="Search the MFP food database by name.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Food search query.",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="mfp_get_food_details",
        description="Get full nutrition details for a food item by MFP ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "mfp_id": {
                    "type": "integer",
                    "description": "MFP food item ID.",
                },
            },
            "required": ["mfp_id"],
        },
    ),
    Tool(
        name="mfp_get_profile",
        description="Get user profile and preferences from MFP.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info("Tool call: %s", name)

    try:
        result: dict[str, Any]

        if name == "mfp_auth_status":
            result = await mfp_auth_status()

        elif name == "mfp_refresh_auth":
            result = await mfp_refresh_auth(
                browser=arguments.get("browser", "auto"),
            )

        elif name == "mfp_get_diary":
            result = await mfp_get_diary(
                date_str=arguments["date"],
            )

        elif name == "mfp_get_nutrition_summary":
            result = await mfp_get_nutrition_summary(
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
            )

        elif name == "mfp_get_goals":
            result = await mfp_get_goals()

        elif name == "mfp_get_measurements":
            result = await mfp_get_measurements(
                measurement=arguments.get("measurement", "Weight"),
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
            )

        elif name == "mfp_search_food":
            result = await mfp_search_food(
                query=arguments["query"],
            )

        elif name == "mfp_get_food_details":
            result = await mfp_get_food_details(
                mfp_id=arguments["mfp_id"],
            )

        elif name == "mfp_get_profile":
            result = await mfp_get_profile()

        else:
            result = {
                "isError": True,
                "error_code": "UNKNOWN_TOOL",
                "message": f"Unknown tool: {name}",
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception:
        logger.exception("Error in tool %s", name)
        error_result = {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "An internal error occurred. Check server logs.",
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def _validate_auth_on_startup() -> bool:
    """Validate authentication on server startup (warning only)."""
    cred = get_credential()
    if not cred.success or not cred.cookies:
        logger.warning("No credential stored. Run 'mfp-mcp auth' to authenticate.")
        return False

    result = await validate_auth(cred.cookies)
    if result.is_valid:
        logger.info("Authentication valid (username: %s)", result.username)
        return True
    else:
        logger.warning("Authentication invalid: %s", result.message)
        return False


async def run_server_async() -> None:
    """Run the MCP server (async)."""
    logger.info("Starting MyFitnessPal MCP Server")

    await _validate_auth_on_startup()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run_server() -> int:
    """Run the MCP server (entry point)."""
    try:
        asyncio.run(run_server_async())
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped")
        return 0
    except Exception:
        logger.exception("Server error")
        return 1
