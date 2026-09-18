import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit

import jwt
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from app.config import settings


@pytest.fixture(scope="session", autouse=True)
def test_database():
    original = settings()
    admin = urlsplit(original.admin_database_url.get_secret_value())
    runtime = urlsplit(original.database_url.get_secret_value())
    if not admin.hostname:
        pytest.fail("Configure PostgreSQL first; integration tests must use real PostgreSQL.")
    test_name = "fraud_investigation_test"
    with psycopg.connect(urlunsplit(admin._replace(path="/postgres")), autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (test_name,)).fetchone():
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_name)))
    old = {
        key: os.environ.get(key)
        for key in (
            "DATABASE_URL",
            "ADMIN_DATABASE_URL",
            "ENABLE_PUBLIC_DEMO",
            "ENABLE_LIVE_GENERATION",
        )
    }
    os.environ["DATABASE_URL"] = urlunsplit(runtime._replace(path="/" + test_name))
    os.environ["ADMIN_DATABASE_URL"] = urlunsplit(admin._replace(path="/" + test_name))
    os.environ["ENABLE_PUBLIC_DEMO"] = "true"
    os.environ["ENABLE_LIVE_GENERATION"] = "false"
    settings.cache_clear()
    from manage import migrate
    from seed import seed

    migrate()
    seed()
    yield
    for key, value in old.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    settings.cache_clear()


@pytest.fixture
def client(test_database):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def analyst_headers(test_database):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "analyst-local",
            "tenant": "demo",
            "iat": now,
            "exp": now + timedelta(minutes=10),
            "iss": "fraud-investigation",
            "aud": "fraud-investigation",
        },
        settings().auth_secret.get_secret_value(),
        algorithm="HS256",
    )
    return {"Authorization": "Bearer " + token}
