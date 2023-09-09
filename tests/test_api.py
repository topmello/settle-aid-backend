import sys
from pathlib import Path
import pytest
import time
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


def test_access_docs(test_client):
    res = test_client.get("/")
    assert res.status_code == 401, "Expected 401 Unauthorized but got another status code"
    assert "WWW-Authenticate" in res.headers, "Expected 'WWW-Authenticate' header in the response"


def test_generate_name(test_client):
    res = test_client.get("/user/generate/")
    assert res.status_code == 200


def test_translate(test_client):
    res = test_client.post("translate", json={
        "texts": ["你好"]
    })
    assert res.status_code == 200
    assert res.json()["results"] == ["Hello"]


def test_create_user(test_client):
    res = test_client.post(
        "/user/", json={"username": "test", "password": "test"})
    if res.status_code == 400:
        assert res.json()["detail"] == "Username already registered"
    if res.status_code == 201:
        assert res.json()["username"] == "test"


def test_login(test_client):
    res = test_client.post(
        "/login/", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"] != None


def test_login_v2(test_client):
    res = test_client.post(
        "/login/v2/", json={"username": "test", "password": "test"})

    assert res.status_code == 200
    assert 'access_token' in res.json()
    assert 'refresh_token' in res.json()
    assert 'token_type' in res.json()
    assert 'access_token_expire' in res.json()
    assert 'refresh_token_expire' in res.json()

    time.sleep(2)

    res = test_client.post(
        "/login/v2/refresh/", json={"refresh_token": res.json()["refresh_token"]})

    assert res.status_code == 200
    assert 'access_token' in res.json()
    assert 'refresh_token' in res.json()
    assert 'token_type' in res.json()
    assert 'access_token_expire' in res.json()
    assert 'refresh_token_expire' in res.json()


def test_route(test_client):
    res = test_client.post(
        "/login/v2/", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    time.sleep(2)

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


def test_route_v2(test_client):
    res = test_client.post(
        "/login/v2/", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    time.sleep(2)

    res = test_client.post(
        "/search/v2/route/",
        headers=headers,
        json={
            "query": ["museum", "Indian", "Warehouse"],
            "negative_query": ["Chinese", "Japanese", "Korean"],
            "location_type": ["landmark", "restaurant", "pharmacy"],
            "longitude": 144.9549,
            "latitude": -37.81803,
            "distance_threshold": 1000,
            "similarity_threshold": 0.1,
            "negative_similarity_threshold": 0.1,
            "route_type": "walking"
        })
    assert res.status_code == 200
    assert len(res.json()["locations"]) == 3

    route_id = res.json()["route_id"]

    res = test_client.get(
        "/route/user/100"
    )
    assert res.status_code == 404

    res = test_client.get(
        f"/route/user/1"
    )
    assert res.status_code == 200

    res = test_client.get(
        f"/route/user/1/?limit=1000"
    )
    assert res.status_code == 400


def test_vote(test_client):
    res = test_client.post(
        "/login/v2/", json={"username": "test", "password": "test"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    time.sleep(2)

    res = test_client.post(
        "/search/v2/route/",
        headers=headers,
        json={
            "query": ["museum", "Indian", "Warehouse"],
            "negative_query": ["Chinese", "Japanese", "Korean"],
            "location_type": ["landmark", "restaurant", "pharmacy"],
            "longitude": 144.9549,
            "latitude": -37.81803,
            "distance_threshold": 1000,
            "similarity_threshold": 0.1,
            "negative_similarity_threshold": 0.1,
            "route_type": "walking"
        })
    assert res.status_code == 200

    route_id = res.json()["route_id"]

    time.sleep(2)

    res = test_client.post(
        "/vote/",
        headers=headers,
        json={
            "route_id": route_id,
            "vote": True
        })
    assert res.status_code == 201

    res = test_client.post(
        "/vote/",
        headers=headers,
        json={
            "route_id": route_id,
            "vote": True
        })

    assert res.status_code == 409

    time.sleep(2)

    res = test_client.get(
        f"/route/{route_id}"
    )

    assert res.status_code == 200
    assert res.json()["num_votes"] == 1

    res = test_client.post(
        "/vote/",
        headers=headers,
        json={
            "route_id": route_id,
            "vote": False
        })

    assert res.status_code == 201

    res = test_client.post(
        "/vote/",
        headers=headers,
        json={
            "route_id": route_id,
            "vote": False
        })

    assert res.status_code == 404
