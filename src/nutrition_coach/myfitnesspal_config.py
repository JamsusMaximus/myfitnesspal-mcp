import os

from dotenv import load_dotenv

load_dotenv()

class MyFitnessPalConfig:
    @staticmethod
    def get_credentials():
        username = os.getenv("MYFITNESSPAL_USERNAME")
        password = os.getenv("MYFITNESSPAL_PASSWORD")
        email = os.getenv("MYFITNESSPAL_EMAIL")
        if not username or not password:
            raise ValueError("MyFitnessPal username and password must be set as environment variables MYFITNESSPAL_USERNAME and MYFITNESSPAL_PASSWORD.")
        return username, password, email

    @staticmethod
    def get_api_keys():
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key must be set as environment variable OPENAI_API_KEY.")
        return openai_api_key

    @staticmethod
    def get_urls():
        login_url = os.getenv("MYFITNESSPAL_LOGIN_URL")
        food_log_url = os.getenv("MYFITNESSPAL_FOOD_LOG_URL")
        if not login_url or not food_log_url:
            raise ValueError("MyFitnessPal login and food log URLs must be set as environment variables MYFITNESSPAL_LOGIN_URL and MYFITNESSPAL_FOOD_LOG_URL.")
        return login_url, food_log_url
