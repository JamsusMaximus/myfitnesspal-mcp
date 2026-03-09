from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import pytest
from nutrition_coach.api_server import app, run_server

client = TestClient(app)

@patch("nutrition_coach.api_server.get_myfitnesspal_day_data")
def test_read_diary_endpoint(mock_get_data):
    # Mock the external call to return some sample data
    mock_get_data.return_value = {"date": "2023-01-01", "calories": 2000}

    response = client.get("/diary/2023/01/01")
    assert response.status_code == 200
    assert response.json() == {"date": "2023-01-01", "calories": 2000}

@patch("nutrition_coach.api_server.uvicorn.run")
def test_run_server_with_port(mock_run):
    # Test default port
    run_server()
    mock_run.assert_called_once_with(app, host="0.0.0.0", port=8000)
    
    # Reset mock
    mock_run.reset_mock()
    
    # Test custom port
    run_server(port=9000)
    mock_run.assert_called_once_with(app, host="0.0.0.0", port=9000)
