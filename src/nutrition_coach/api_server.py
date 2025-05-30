import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from nutrition_coach.myfitnesspal_scrape_food_log import get_myfitnesspal_day_data, MyFitnessPalCookieError

app = FastAPI()

# Create FastMCP instance
mcp_server = FastMCP(name="NutritionCoachServer", stateless_http=True)

# Define an example tool
@mcp_server.tool(description="A simple echo tool")
def echo(message: str) -> str:
    return f"Echo: {message}"

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
