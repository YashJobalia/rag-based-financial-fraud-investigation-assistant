from fastapi import HTTPException

from .db import connection


def reserve_request(user):
    """Shared per-principal minute budget. Anonymous demo visitors share one budget."""
    with connection(user.tenant, user.actor) as conn:
        reserved = conn.execute(
            """INSERT INTO request_budgets(tenant_id,actor,minute)
           VALUES(%s,%s,date_trunc('minute',now()))
           ON CONFLICT(tenant_id,actor,minute) DO UPDATE
           SET requests=request_budgets.requests+1 WHERE request_budgets.requests<60
           RETURNING requests""",
            (user.tenant, user.actor),
        ).fetchone()
        if reserved is None:
            raise HTTPException(
                429, "This session's request budget is exhausted. Retry next minute."
            )
