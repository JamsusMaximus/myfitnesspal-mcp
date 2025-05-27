from flask import Flask, request, jsonify
from nutrition_coach.myfitnesspal_scrape_food_log import get_myfitnesspal_day_data, MyFitnessPalCookieError

app = Flask(__name__)

@app.route('/diary/<int:year>/<int:month>/<int:day>', methods=['GET'])
def get_diary_data(year, month, day):
    try:
        data = get_myfitnesspal_day_data(year, month, day)
        if data:
            return jsonify(data), 200
        elif data is None:
            error_message = {"error": "Failed to retrieve data from MyFitnessPal for the specified date."}
            return jsonify(error_message), 500
    except MyFitnessPalCookieError:
        error_message = {"error": "Failed to load MyFitnessPal cookies. Please ensure you are logged in via a supported browser."}
        return jsonify(error_message), 503
    except Exception as e:
        error_message = {"error": f"An unexpected error occurred: {str(e)}"}
        return jsonify(error_message), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)