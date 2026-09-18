# RAG-Based Financial Fraud Investigation Assistant

An analyst assistant for investigating suspected account takeover using structured analysis and evidence-grounded retrieval.

## Status

Planning foundation only. The private [GitHub repository](https://github.com/YashJobalia/rag-based-financial-fraud-investigation-assistant) has been created. The application, database, Vercel deployment, and custom domain have not been implemented or verified yet. No quality or performance results are claimed.

## Agreed direction

- Frontend: React, Vite, TypeScript.
- Backend: FastAPI and Pydantic.
- Data: PostgreSQL with full-text search and pgvector. Hosting/authentication choice remains open.
- Model provider: OpenAI, with credentials confined to the backend.
- GitHub repository target: `YashJobalia/rag-based-financial-fraud-investigation-assistant`.
- Deployment target: React and FastAPI on Vercel after verification.
- Public address: `https://fraud-investigation.yashjobalia.com` after domain setup.
- Separate repository, environment, and database from CareLine. Do not modify CareLine.

All demonstration records will be synthetic. Procedures and historical reports will be explicitly fictional. Analysts make the final decision; the system cannot freeze accounts, block payments, or determine criminality.

See [the design plan](docs/design.md) for scope and acceptance criteria, and [deployment and secrets](docs/deployment.md) for the deployment requirements.
