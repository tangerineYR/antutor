import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from main import app

@pytest.mark.parametrize("origin", [None, "https://attacker.pages.dev"])
def test_websocket_rejects_untrusted_origin(origin):
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/chat", headers={"origin": origin} if origin else {}): pass
        assert exc.value.code == 1008

def test_websocket_requires_token_on_allowed_origin():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/chat", headers={"origin": "http://localhost:3000"}) as ws:
            ws.send_json({})
            assert ws.receive_json()["type"] == "error"
            with pytest.raises(WebSocketDisconnect): ws.receive_json()
