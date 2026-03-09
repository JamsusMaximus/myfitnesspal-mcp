"""mfp_get_nutrition_summary - Get nutrition totals for a date range."""

import logging
from datetime import timedelta
from typing import Any

from pydantic import ValidationError

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError
from mfp_mcp.tools._validation import DateRangeInput, format_validation_error

logger = logging.getLogger("mfp-mcp")


async def mfp_get_nutrition_summary(
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Get nutrition summary for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Dict with daily summaries and averages.
    """
    try:
        validated = DateRangeInput(start_date=start_date, end_date=end_date)
    except ValidationError as e:
        return {
            "isError": True,
            "error_code": "VALIDATION_ERROR",
            "message": format_validation_error(e),
        }

    try:
        client = MFPClient()
        days = []
        current = validated.start_date

        while current <= validated.end_date:
            diary = await client.get_diary(current)
            has_entries = any(m.get("entries") for m in diary.get("meals", []))
            days.append({
                "date": current.isoformat(),
                "totals": diary.get("totals", {}),
                "complete": has_entries,
            })
            current += timedelta(days=1)

        # Calculate averages across days with data
        complete_days = [d for d in days if d["complete"]]
        averages: dict[str, float] = {}
        if complete_days:
            all_keys: set[str] = set()
            for d in complete_days:
                all_keys.update(d["totals"].keys())
            for key in all_keys:
                values = [d["totals"].get(key, 0) for d in complete_days]
                averages[key] = round(sum(values) / len(values), 1)

        return {
            "start_date": validated.start_date.isoformat(),
            "end_date": validated.end_date.isoformat(),
            "days": days,
            "averages": averages,
            "days_with_data": len(complete_days),
            "total_days": len(days),
        }

    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
    except Exception:
        logger.exception("Error fetching nutrition summary")
        return {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "Failed to fetch nutrition summary. Check server logs.",
        }
