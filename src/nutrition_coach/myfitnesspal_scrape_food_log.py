
import browser_cookie3
import myfitnesspal
# from myfitnesspal import MyFitnessPalException # Removed problematic import

from .myfitnesspal_config import MyFitnessPalConfig # This import is no longer strictly needed if not using credentials


class MyFitnessPalCookieError(Exception):
    """Custom exception for MyFitnessPal cookie loading errors."""
    pass


def get_myfitnesspal_day_data(year: int, month: int, day: int) -> dict | None:
    """
    Fetches MyFitnessPal data for a specific day using browser cookies.

    Args:
        year: The year of the date to fetch.
        month: The month of the date to fetch.
        day: The day of the date to fetch.

    Returns:
        A dictionary containing the day's nutrition data, or None if a data fetching error occurs
        (other than cookie loading issues).
        The dictionary structure is:
        {
            "date_str": "YYYY-MM-DD",
            "meals_data": {
                "MealName1": [{"name": "Food1", "totals": {...}}, ...],
                ...
            },
            "day_totals": {...},
            "water": float,
            "notes": str
        }

    Raises:
        MyFitnessPalCookieError: If browser cookies cannot be loaded.
    """
    client = None
    loaded_cookie_jar = None

    try:
        # Attempt to load cookies from all supported browsers
        loaded_cookie_jar = browser_cookie3.load()
        if not (loaded_cookie_jar and len(loaded_cookie_jar) > 0):
            loaded_cookie_jar = None  # Ensure it's None if no cookies found
    except Exception as e: # Catching broad exception from browser_cookie3
        loaded_cookie_jar = None
        # Optionally, could re-raise or wrap 'e' in MyFitnessPalCookieError for more details
        # For now, just setting to None and letting the next block handle it.

    if loaded_cookie_jar:
        client = myfitnesspal.Client(cookiejar=loaded_cookie_jar)
    else:
        raise MyFitnessPalCookieError(
            "Failed to load browser cookies for MyFitnessPal. "
            "Please ensure you are logged into MyFitnessPal in a supported browser, "
            "that the browser is closed, and that cookies can be accessed. "
            "Alternatively, ensure your browser's cookie database is not locked."
        )

    try:
        day_data = client.get_date(year, month, day)

        if not day_data:
            return None # Should ideally not happen if client.get_date itself raises on error

        return {
            "date_str": f"{year:04d}-{month:02d}-{day:02d}",
            "meals_data": {
                meal.name: [
                    {"name": entry.name, "totals": entry.totals}
                    for entry in meal.entries
                ]
                for meal in day_data.meals
            },
            "day_totals": day_data.totals,
            "water": day_data.water,
            "notes": day_data.notes,
        }
    # except MyFitnessPalException: # Removed specific exception catch due to import issues
    #     # Handles errors from the myfitnesspal library during data fetching (e.g., API changes, network issues)
    #     # Log the exception here if needed
    #     return None
    except Exception: # This will now catch errors previously intended for MyFitnessPalException
        # Handles errors from the myfitnesspal library during data fetching (e.g., API changes, network issues)
        # as well as other unexpected errors during data processing
        # Log the exception here if needed
        return None

# Example usage (optional, can be removed or kept for testing)
if __name__ == "__main__":
    # This part will only run when the script is executed directly
    # For example, to test the function:
    try:
        data = get_myfitnesspal_day_data(2025, 5, 27)
        if data:
            import json
            print(json.dumps(data, indent=4))
        else:
            # This else block might be reached if get_date returns None without an exception,
            # or if MyFitnessPalException/Exception occurs and returns None.
            print("Failed to retrieve data (returned None).")
    except MyFitnessPalCookieError as e:
        print(f"Cookie Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
