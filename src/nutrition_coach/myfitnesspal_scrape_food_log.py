
import browser_cookie3
import myfitnesspal
import os
from http.cookiejar import MozillaCookieJar
# from myfitnesspal import MyFitnessPalException # Removed problematic import

# from .myfitnesspal_config import MyFitnessPalConfig # This import is no longer strictly needed if not using credentials


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
    file_load_outcome = None
    browser_load_outcome = None

    cookie_file_path = os.getenv("MYFITNESSPAL_COOKIE_FILE")

    if cookie_file_path:
        print(f"Attempting to load cookies from MYFITNESSPAL_COOKIE_FILE: {cookie_file_path}")
        try:
            cj = MozillaCookieJar()
            cj.load(cookie_file_path, ignore_discard=True, ignore_expires=True)
            if cj and len(cj) > 0:
                loaded_cookie_jar = cj
                print(f"Successfully loaded cookies from file: {cookie_file_path}")
            else:
                print(f"Cookie file '{cookie_file_path}' was empty or invalid. Falling back.")
                file_load_outcome = f"File '{cookie_file_path}' was empty or invalid"
        except FileNotFoundError:
            print(f"Cookie file '{cookie_file_path}' not found. Falling back.")
            file_load_outcome = f"File '{cookie_file_path}' not found"
        except Exception as e:
            print(f"Error loading cookies from file '{cookie_file_path}': {e}. Falling back.")
            file_load_outcome = f"Error loading from file '{cookie_file_path}': {e}"

    if not loaded_cookie_jar:
        if not cookie_file_path:
            print("MYFITNESSPAL_COOKIE_FILE not set. Attempting to load cookies using browser_cookie3.")
        else: # Implies file attempt was made and failed (or didn't load cookies)
            print("Falling back to browser_cookie3.")

        try:
            cj_browser = browser_cookie3.load()
            if cj_browser and len(cj_browser) > 0:
                loaded_cookie_jar = cj_browser
                print("Successfully loaded cookies using browser_cookie3.")
            else:
                print("browser_cookie3 found no cookies.")
                browser_load_outcome = "browser_cookie3 found no cookies"
        except Exception as e:
            print(f"Error loading cookies using browser_cookie3: {e}")
            browser_load_outcome = f"browser_cookie3 failed with error: {e}"

    if loaded_cookie_jar:
        client = myfitnesspal.Client(cookiejar=loaded_cookie_jar)
    else:
        error_summary_parts = []
        if cookie_file_path:
            if file_load_outcome:
                error_summary_parts.append(f"Attempt via MYFITNESSPAL_COOKIE_FILE ('{cookie_file_path}'): {file_load_outcome}")
            # If file_load_outcome is None here, it means the file was specified,
            # but the try-except block for file loading didn't set an outcome.
            # This implies it didn't hit an exception or the "empty/invalid" condition,
            # yet loaded_cookie_jar is still None. This scenario should be rare if logic is correct.
            # We'll implicitly cover this by checking browser_load_outcome next.

            if browser_load_outcome: # This means fallback to browser_cookie3 happened and had a specific outcome
                error_summary_parts.append(f"Fallback via browser_cookie3: {browser_load_outcome}")
            elif file_load_outcome : # File attempt failed, and browser_cookie3 was tried but didn't set browser_load_outcome (e.g. returned None without error)
                error_summary_parts.append("Fallback via browser_cookie3 also failed or yielded no cookies")
        else: # MYFITNESSPAL_COOKIE_FILE was not set, so only browser_cookie3 was attempted
            if browser_load_outcome:
                error_summary_parts.append(f"Attempt via browser_cookie3: {browser_load_outcome}")
            else: # Only browser_cookie3 was tried and it failed or yielded no cookies without a specific error string
                error_summary_parts.append("Attempt via browser_cookie3 failed or yielded no cookies")
        
        detailed_failure_description = ". ".join(filter(None, error_summary_parts)) # filter(None,...) handles if a part is empty
        if not detailed_failure_description: # Should not happen if we reach here, but as a safeguard
            detailed_failure_description = "Unknown error loading cookies"
        elif not detailed_failure_description.endswith('.'):
            detailed_failure_description += "."

        error_message = (
            f"Failed to load MyFitnessPal cookies. Details: [{detailed_failure_description}] "
            "If using a cookie file, ensure it is a valid Netscape-format cookie file. "
            "If using browser cookies, please ensure you are logged into MyFitnessPal in a supported browser, "
            "that the browser is closed, and that cookies can be accessed. "
            "Alternatively, ensure your browser's cookie database is not locked."
        )
        raise MyFitnessPalCookieError(error_message)

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
