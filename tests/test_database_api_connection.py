import os
import pytest
import psycopg2
from fastapi.testclient import TestClient
from main import app, get_db  # Import your FastAPI app and DB dependency

# Create a test client
client = TestClient(app)

# Test database connection
def test_db_connection():
    """Test if the database connection is successful."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432)
        )
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

# Test API connection
def test_load_chat():
    """Test if the FastAPI `/load_chat/` endpoint returns a 200 response."""
    response = client.get("/load_chat/")
    assert response.status_code == 200
