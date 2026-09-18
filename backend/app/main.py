from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .auth import Principal, principal, require_analyst
from .briefs import generate
from .config import settings
from .db import connection
from .evidence import case_access, case_evidence, resolve, visible_chunks
from .models import BriefRequest, ReviewRequest, SearchRequest
from .limits import reserve_request
from .retrieval import retrieve

app = FastAPI(title="RAG-Based Financial Fraud Investigation Assistant", version="0.1.0")


@app.middleware("http")
async def secure_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(Exception)
async def error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "The service is temporarily unavailable. Check backend configuration."},
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0", "synthetic": True}


@app.get("/api/session")
def session(user: Principal = Depends(principal)):
    return {
        "actor": user.actor,
        "role": user.role,
        "synthetic": True,
        "retrieval_modes": ["keyword"],
        "live_available": user.role == "analyst"
        and settings().enable_live_generation
        and bool(settings().openai_api_key.get_secret_value()),
    }


@app.get("/api/cases")
def cases(user: Principal = Depends(principal)):
    with connection(user.tenant, user.actor) as conn:
        return conn.execute(
            """SELECT c.*,a.display_name FROM cases c
            JOIN accounts a ON a.tenant_id=c.tenant_id AND a.id=c.account_id
            JOIN case_assignments ca ON ca.tenant_id=c.tenant_id AND ca.case_id=c.id
            WHERE ca.actor=%s ORDER BY c.opened_at DESC,c.id""",
            (user.actor,),
        ).fetchall()


@app.get("/api/cases/{case_id}")
def detail(case_id: str, user: Principal = Depends(principal)):
    with connection(user.tenant, user.actor) as conn:
        case = case_access(conn, case_id, user)
        return {"case": case, **case_evidence(conn, case), "synthetic": True}


@app.get("/api/cases/{case_id}/evidence/{evidence_id:path}")
def evidence(case_id: str, evidence_id: str, user: Principal = Depends(principal)):
    with connection(user.tenant, user.actor) as conn:
        case = case_access(conn, case_id, user)
        return resolve(conn, case, user, evidence_id)


@app.get("/api/cases/{case_id}/documents")
def documents(case_id: str, user: Principal = Depends(principal)):
    with connection(user.tenant, user.actor) as conn:
        return visible_chunks(conn, case_access(conn, case_id, user), user)


@app.post("/api/cases/{case_id}/retrieve")
def search(case_id: str, body: SearchRequest, user: Principal = Depends(principal)):
    reserve_request(user)
    with connection(user.tenant, user.actor) as conn:
        return retrieve(conn, case_access(conn, case_id, user), user, body.query, body.mode, body.k)


@app.post("/api/cases/{case_id}/briefs")
def brief(case_id: str, body: BriefRequest, user: Principal = Depends(principal)):
    reserve_request(user)
    return generate(case_id, body, user)


@app.get("/api/cases/{case_id}/reviews")
def reviews(case_id: str, user: Principal = Depends(principal)):
    require_analyst(user)
    with connection(user.tenant, user.actor) as conn:
        case_access(conn, case_id, user)
        return conn.execute(
            "SELECT id,brief_id,disposition,notes,created_at,actor FROM reviews WHERE case_id=%s ORDER BY created_at DESC",
            (case_id,),
        ).fetchall()


@app.post("/api/cases/{case_id}/reviews", status_code=201)
def review(case_id: str, body: ReviewRequest, user: Principal = Depends(principal)):
    require_analyst(user)
    with connection(user.tenant, user.actor) as conn:
        case_access(conn, case_id, user)
        if not conn.execute(
            "SELECT 1 FROM briefs WHERE id=%s AND case_id=%s", (body.brief_id, case_id)
        ).fetchone():
            raise HTTPException(404, "Brief not found")
        row = conn.execute(
            """INSERT INTO reviews(id,tenant_id,case_id,actor,brief_id,disposition,notes)
            VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id,created_at""",
            (
                str(uuid4()),
                user.tenant,
                case_id,
                user.actor,
                body.brief_id,
                body.disposition,
                body.notes,
            ),
        ).fetchone()
        conn.execute(
            "INSERT INTO audit_events(tenant_id,actor,case_id,action) VALUES(%s,%s,%s,'review.saved')",
            (user.tenant, user.actor, case_id),
        )
        return {**row, "message": "Review saved. No account or payment action was taken."}
