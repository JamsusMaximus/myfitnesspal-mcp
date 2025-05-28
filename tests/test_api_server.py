from fastapi.testclient import TestClient
from unittest.mock import patch
from nutrition_coach.api_server import app

client = TestClient(app)

@patch("nutrition_coach.api_server.get_myfitnesspal_day_data")
def test_read_diary_endpoint(mock_get_data):
    # Mock the external call to return some sample data
    mock_get_data.return_value = {"date": "2023-01-01", "calories": 2000}

    response = client.get("/diary/2023/01/01")
    assert response.status_code == 200
    assert response.json() == {"date": "2023-01-01", "calories": 2000}