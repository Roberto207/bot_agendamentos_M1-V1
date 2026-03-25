"""
Módulo de testes automatizados para o Agente IA Orquestrador.
Contém testes para assegurar que a rota do webhook responda de forma coerente.
"""
from fastapi.testclient import TestClient
from ai_whatsapp_orchestrator import app

# Inicializa o cliente de testes do FastAPI
client = TestClient(app)

def test_webhook_estrutura_invalida():
    """
    Testa se o webhook rejeita payloads que não contenham 'from' ou 'message',
    garantindo que não haverá quebra no parser do fluxo conversacional com o Groq.
    """
    response = client.post("/webhook/whatsapp/TEST_API_KEY", json={"outro_parametro": "valor qualquer"})
    
    # Verifica se o código retornado foi Error 400 (Bad Request)
    assert response.status_code == 400
    # Checa se o corpo da resposta possui a mensagem de erro esperada
    assert "Missing 'from' or 'message'" in response.json()["detail"]
