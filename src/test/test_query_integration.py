from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_exito_con_datos():
    """
    IT_QRY_001 – Éxito con datos.
    """
    body = {
        "user_id": 1,
        "document_type_id": "CC",
        "document_number": "123456",
        "question": "¿Qué diagnósticos tiene el paciente?",
    }

    response = client.post("/query", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "no_data")
    assert "answer" in data
