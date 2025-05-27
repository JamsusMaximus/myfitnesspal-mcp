
import browser_cookie3
import myfitnesspal

from .myfitnesspal_config import MyFitnessPalConfig

# import requests # Not directly needed here anymore unless manipulating session further

username, password, _ = MyFitnessPalConfig.get_credentials()
loaded_cookie_jar = None
client = None

# Attempt to load cookies from Firefox
print("Attempting to load Firefox browser cookies...")
try:
    loaded_cookie_jar = browser_cookie3.firefox()
    if loaded_cookie_jar is not None and len(loaded_cookie_jar) > 0:
        print(f"Successfully loaded {len(loaded_cookie_jar)} cookies from Firefox.")
    else:
        print("No cookies found in Firefox or failed to load.")
        loaded_cookie_jar = None # Ensure it's None if no cookies
except Exception as e:
    print(f"Error loading Firefox cookies: {e}.")
    loaded_cookie_jar = None

# Initialize the client
print("Initializing MyFitnessPal client...")
if loaded_cookie_jar:
    print("Using loaded Firefox cookies for client session.")
    client = myfitnesspal.Client(cookiejar=loaded_cookie_jar)
else:
    print("No browser cookies loaded or error during loading. Using username/password for login.")
    client = myfitnesspal.Client(username=username, password=password)

# Proceed to fetch data.
try:
    print("Fetching data for 2025-05-26...")
    # The username argument in get_date is typically for when the client isn't tied to a user yet.
    # If login via credentials or cookies was successful, it should know the user.
    day = client.get_date(2025, 5, 26)
    print("Data fetched successfully.")
    print(day)
except myfitnesspal.exceptions.MyFitnessPalException as e:
    print(f"MyFitnessPal API Error: {e}")
    print("This could be due to authentication issues (e.g., invalid session from cookies, or login failed) or other API problems.")
except Exception as e:
    print(f"Error fetching data from MyFitnessPal: {e}")