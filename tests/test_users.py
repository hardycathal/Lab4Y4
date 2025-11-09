import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.models import Base
from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool,)

TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # hand the client to the test
        yield c
        # --- teardown happens when the 'with' block exits ---

def test_create_user(client):
    r = client.post("/api/users", 
json={"name":"Paul","email":"pl@atu.ie","age":25,"student_id":"S1234567"})
    assert r.status_code == 201

def test_put_user(client):
    # create user
    r = client.post("/api/users", json={
        "name": "Old Name",
        "email": "old@example.com",
        "age": 25,
        "student_id": "S1234566"
    })
    assert r.status_code == 201
    user_id = r.json()["id"]

    # full update with PUT
    r2 = client.put(f"/api/users/{user_id}", json={
        "name": "New Name",
        "email": "new@example.com",
        "age": 30,
        "student_id": "S7654321"
    })
    assert r2.status_code == 200
    body = r2.json()
    assert body["name"] == "New Name"
    assert body["email"] == "new@example.com"
    assert body["age"] == 30

def test_patch_user(client):
    r = client.post("/api/users", json={
        "name": "Patch Me",
        "email": "patch@example.com",
        "age": 22,
        "student_id": "S1111111"
    })
    assert r.status_code == 201
    user_id = r.json()["id"]

    # partial update with PATCH (only name)
    r2 = client.patch(f"/api/users/{user_id}", json={"name": "Patched Name"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["name"] == "Patched Name"
    # make sure other fields unchanged
    assert body["email"] == "patch@example.com"
