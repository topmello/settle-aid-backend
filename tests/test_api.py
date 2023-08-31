import sys
from pathlib import Path

# add the project directory to the sys.path
project_dir = str(Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from fastapi.testclient import TestClient  # noqa
from app.main import app  # noqa


client = TestClient(app)


def test_root():
    print("Hello World")
    # print(sys.path)
    # res = client.get("/")
    # print(res.json())
    # assert res.status_code == 200
