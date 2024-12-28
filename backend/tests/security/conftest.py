import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app

# Mock OpenAI client
import sys
from unittest.mock import patch

# Mock the OpenAI client before importing app
mock_openai = MagicMock()
mock_openai.chat.completions.create.return_value = MagicMock(
    choices=[MagicMock(message=MagicMock(content="Mocked response"))]
)

with patch.dict('sys.modules', {'openai': mock_openai}):
    from backend.app.main import app

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_redis():
    return MagicMock()