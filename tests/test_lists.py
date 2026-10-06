import pytest
from fastapi.testclient import TestClient

from app import lists
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(lists, "DATA_FILE", tmp_path / "lists.json")
    return TestClient(app)


def sample(list_id="l1", kind="lista", name="Mercado"):
    return {
        "id": list_id, "name": name, "kind": kind, "total": 34890, "savings": 25200,
        "items": [{"query": "detergente fab", "type": "Detergente en polvo", "qty": 1,
                   "name": "Detergente Fab 5kg", "store": "jumbo", "price": 34890,
                   "size_qty": 5000, "size_unit": "g", "unit_price": 6978, "unit_price_label": "kg"}],
    }


def test_create_list_and_read_back(client):
    assert client.get("/api/lists").json() == {"lists": []}
    r = client.put("/api/lists/l1", json=sample())
    assert r.status_code == 200
    saved = client.get("/api/lists").json()["lists"]
    assert [l["name"] for l in saved] == ["Mercado"]
    assert saved[0]["created_at"] and saved[0]["updated_at"]


def test_update_keeps_created_at(client):
    first = client.put("/api/lists/l1", json=sample()).json()
    second = client.put("/api/lists/l1", json=sample(name="Mercado del mes")).json()
    assert second["created_at"] == first["created_at"]
    assert [l["name"] for l in client.get("/api/lists").json()["lists"]] == ["Mercado del mes"]


def test_delete(client):
    client.put("/api/lists/l1", json=sample())
    assert client.delete("/api/lists/l1").status_code == 200
    assert client.delete("/api/lists/l1").status_code == 404
    assert client.get("/api/lists").json()["lists"] == []


def test_rejects_bad_input(client):
    assert client.put("/api/lists/otro", json=sample()).status_code == 400  # id distinto
    assert client.put("/api/lists/l1", json={**sample(), "items": []}).status_code == 422
    assert client.put("/api/lists/../x", json=sample("../x")).status_code in (404, 422)


def test_old_purchases_trimmed_but_named_lists_kept(client, monkeypatch):
    monkeypatch.setattr(lists, "MAX_LISTS", 3)
    client.put("/api/lists/keep", json=sample("keep", "lista"))
    for n in range(4):
        client.put(f"/api/lists/c{n}", json=sample(f"c{n}", "compra"))
    ids = {l["id"] for l in client.get("/api/lists").json()["lists"]}
    assert len(ids) == 3 and "keep" in ids and "c0" not in ids
