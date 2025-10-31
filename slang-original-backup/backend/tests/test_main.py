from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


