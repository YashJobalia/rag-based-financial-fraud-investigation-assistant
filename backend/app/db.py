from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def connection(tenant: str, actor: str):
    """Each request gets a transaction-local security context; never shared across users."""
    with psycopg.connect(
        settings().database_url.get_secret_value(), row_factory=dict_row, connect_timeout=5
    ) as conn:
        conn.execute("SELECT set_config('app.tenant', %s, true)", (tenant,))
        conn.execute("SELECT set_config('app.actor', %s, true)", (actor,))
        conn.execute("SET LOCAL statement_timeout = '5s'")
        yield conn
