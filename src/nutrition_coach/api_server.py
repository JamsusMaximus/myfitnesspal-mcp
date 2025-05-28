from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from nutrition_coach.myfitnesspal_scrape_food_log import get_myfitnesspal_day_data, MyFitnessPalCookieError

app = FastAPI()

@app.get('/diary/{year}/{month}/{day}')
async def get_diary_data(year: int, month: int, day: int):
    try:
        data = get_myfitnesspal_day_data(year, month, day)
        if data:
            return data
        elif data is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve data from MyFitnessPal for the specified date.")
    except MyFitnessPalCookieError:
        raise HTTPException(status_code=503, detail="Failed to load MyFitnessPal cookies. Please ensure you are logged in via a supported browser.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")