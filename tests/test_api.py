import sys
from pathlib import Path

# add the project directory to the sys.path
project_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from fastapi.testclient import TestClient  # noqa
from app.main import app  # noqa


client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200


def test_generate_name():
    res = client.get("/user/generate/")
    assert res.status_code == 200


def test_create_user():
    res = client.post("/user/", json={"username": "test", "password": "test"})
    if res.status_code == 400:
        assert res.json()["detail"] == "Email already registered"
    if res.status_code == 201:
        assert res.json()["username"] == "test"


def test_login():
    res = client.post("/login", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"] != None
