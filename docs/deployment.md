# Deployment and secret handling

## Authorized destination

- GitHub repository: `YashJobalia/rag-based-financial-fraud-investigation-assistant`.
- Full project title: RAG-Based Financial Fraud Investigation Assistant.
- Both React/Vite and FastAPI will be deployed to Vercel after the application is verified.
- Custom domain: `fraud-investigation.yashjobalia.com`.
- Do not modify the main portfolio, CareLine, root-domain DNS, or unrelated services.
- Do not provision paid services without authorization.

The user confirmed `YashJobalia` as the repository owner. Local Git credentials were verified against the GitHub API as `YashJobalia`, and the private repository was created under that account. The GitHub connector uses a different account and should not be used for this repository unless reconnected. The connected Vercel team listing returned an empty list; deployment account access has not yet been established. No Vercel or DNS resources have been created.

## Hosting design

Prefer same-origin routing: `/` serves React and `/api` serves FastAPI. Vercel supports FastAPI functions. Its Services configuration also supports multiple runtime entrypoints but is beta; choose the final layout after a minimal build/deployment verification. A single FastAPI project with Vite assets served through the CDN is another documented option.

PostgreSQL must remain persistent outside application function filesystems. Select the hosted database separately; local PostgreSQL data cannot serve a deployed application. Run seed/ingestion/indexing as explicit commands, not on every request or serverless startup.

Domain connection requires access to the owning Vercel project and authoritative DNS. Add only the requested subdomain record using the host-provided target. Do not invent DNS targets or change nameservers. Verify HTTPS, React deep links, API health, authorized evidence access, citation resolution, and generation on the final URL.

## OpenAI key

1. Keep the key out of chat, committed files, commands containing literal values, screenshots, browser storage, and logs.
2. When live integration is ready, copy `backend/.env.example` to `backend/.env` and enter the key locally as `OPENAI_API_KEY`.
3. The backend must explicitly load this file locally. Creating it alone does not configure an application.
4. Never use `VITE_OPENAI_API_KEY`: Vite client-exposed configuration is public.
5. For deployment, enter `OPENAI_API_KEY` as a sensitive server-side Vercel environment variable through the dashboard or secure interactive input.
6. Verify presence and successful usage without printing the value. Disable request/authorization-header logging and sanitize errors.
7. Commit only blank placeholder examples; check ignore rules and scan staged changes before pushing. Exclude local secret files from deployment uploads as well.

The key is not needed during planning. Keep live calls disabled until authentication/authorization, request limits, and usage accounting are implemented.

## Current primary documentation

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/services
- https://vite.dev/guide/static-deploy.html

Consult current documentation again when selecting the exact implementation and deployment configuration.
