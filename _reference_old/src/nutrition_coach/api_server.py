import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from nutrition_coach.myfitnesspal_scrape_food_log import get_myfitnesspal_day_data, MyFitnessPalCookieError

app = FastAPI()

# Create FastMCP instance
mcp_server = FastMCP(name="NutritionCoachServer", stateless_http=True)

# MCP tool to fetch diary data
@mcp_server.tool(description="Get MyFitnessPal food diary data for a specific date. Returns meals, nutrition totals, water intake, and notes.")
def get_diary(date: str) -> str:
    """Fetch MyFitnessPal diary for a given date.

    Args:
        date: Date in YYYY-MM-DD format (e.g. '2026-03-08')
    """
    import json
    parts = date.split("-")
    if len(parts) != 3:
        return "Error: date must be in YYYY-MM-DD format"
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return "Error: date must be in YYYY-MM-DD format"
    try:
        data = get_myfitnesspal_day_data(year, month, day)
        if data:
            return json.dumps(data, indent=2, default=str)
        else:
            return "No data found for that date."
    except MyFitnessPalCookieError as e:
        return f"Cookie error: {e}"
    except Exception as e:
        return f"Error: {e}"

# Mount MCP server
app.mount("/mcp", mcp_server.streamable_http_app())

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

def run_server(port: int = 8000):
    """Run the FastAPI server with the specified port"""
    uvicorn.run(app, host="0.0.0.0", port=port)
