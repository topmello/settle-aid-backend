import sys
from pathlib import Path
import pytest
# add the project directory to the sys.path
project_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from fastapi.testclient import TestClient  # noqa
from app.main import app  # noqa
import scripts.insert_data  # noqa
from alembic import command  # noqa
from alembic.config import Config  # noqa


client = TestClient(app)
alembic_config = Config("alembic.ini")


@pytest.fixture(scope="module")
def test_client():
    print("Setting up test client...")
    command.upgrade(alembic_config, "head")
    scripts.insert_data.main()
    print("Running tests...")
    with TestClient(app) as testing_client:
        yield testing_client
    command.downgrade(alembic_config, "base")


def test_root(test_client):

    res = test_client.get("/")
    assert res.status_code == 200


def test_generate_name(test_client):
    res = test_client.get("/user/generate/")
    assert res.status_code == 200


def test_translate(test_client):
    res = test_client.post("translate", json={
        "text": ["你好"]
    })
    assert res.status_code == 200
    assert res.json()["result"] == "Hello"


def test_create_user(test_client):
    res = test_client.post(
        "/user/", json={"username": "test", "password": "test"})
    if res.status_code == 400:
        assert res.json()["detail"] == "Email already registered"
    if res.status_code == 201:
        assert res.json()["username"] == "test"


def test_login(test_client):
    res = test_client.post(
        "/login", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"] != None


def test_route(test_client):
    res = test_client.post(
        "/login", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = test_client.post(
        "/search/route",
        headers=headers,
        json={
            "query": ["museum", "Indian", "Warehouse"],
            "location_type": ["landmark", "restaurant", "pharmacy"],
            "longitude": 144.9549,
            "latitude": -37.81803,
            "distance_threshold": 500,
            "similarity_threshold": 0,
            "route_type": "walking"
        })
    assert res.status_code == 200
    assert len(res.json()["locations"]) == 3
