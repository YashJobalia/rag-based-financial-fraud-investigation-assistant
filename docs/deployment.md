# Deployment and secret handling

## Authorized destination

- GitHub repository: `YashJobalia/rag-based-financial-fraud-investigation-assistant`.
- Full project title: RAG-Based Financial Fraud Investigation Assistant.
- Both React/Vite and FastAPI will be deployed to Vercel after the application is verified.
- Custom domain: `fraud-investigation.yashjobalia.com`.
- Do not modify the main portfolio, CareLine, root-domain DNS, or unrelated services.
- Do not provision paid services without authorization.

The private repository exists under the confirmed `YashJobalia` account. The GitHub connector uses a different account, so this project uses verified local Git credentials. Although the Vercel connector returned no teams, authenticated local access has now confirmed `yashjobalia` and the `yash-jobalias-projects` team. No Vercel or DNS resources have been created. Hosted PostgreSQL remains pending the user's choice of a separate free Supabase project or a dedicated connection.

## Hosting design

The prepared configuration uses one FastAPI Vercel project: `/` serves React assets and `/api` serves the Python API. Root `app.py` mounts the built `frontend/dist` directory after API routes; Vercel's documented FastAPI static-file support promotes assets to its CDN. This avoids the beta Services feature. Root `requirements.txt` is exported from the backend lockfile; the frontend installs from its own npm lockfile. `vercel.json` sets the build commands and a 60-second function limit. The configuration still requires a real preview build; verify that Python dependency installation and the custom Node build commands both run correctly.

PostgreSQL must remain persistent outside application function filesystems. The local database cannot serve a deployed application. Use a dedicated database, TLS, and a suitable connection pooler. Apply migrations and seed explicitly using an administrative connection; never run them on function startup. Only the restricted runtime database URL belongs in Vercel. Never upload `ADMIN_DATABASE_URL`, local analyst tokens, or local database files.

Domain connection requires access to the owning Vercel project and authoritative DNS. Add only the requested subdomain record using the host-provided target. Do not invent DNS targets or change nameservers. Verify HTTPS, React deep links, API health, authorized evidence access, citation resolution, and generation on the final URL.

## OpenAI key

1. Keep the key out of chat, committed files, commands containing literal values, screenshots, browser storage, and logs.
2. The local helper has prepared an ignored `backend/.env`. Enter the key as `OPENAI_API_KEY` in that file; do not replace the generated database credentials or signing secret.
3. The backend loads this file through Pydantic Settings. Enable `ENABLE_LIVE_GENERATION=true` and restart the backend when ready for a real model test.
4. Never use `VITE_OPENAI_API_KEY`: Vite client-exposed configuration is public.
5. For deployment, enter `OPENAI_API_KEY` as a sensitive server-side Vercel environment variable through the dashboard or secure interactive input.
6. Verify presence and successful usage without printing the value. Disable request/authorization-header logging and sanitize errors.
7. Commit only blank placeholder examples; check ignore rules and scan staged changes before pushing. Exclude local secret files from deployment uploads as well.

Live generation is implemented but untested with a real key. Analyst authorization and a PostgreSQL-enforced daily attempt budget gate calls. Public retrieval/reference requests share a per-minute demo budget; heavy anonymous use can throttle other visitors. Authentication is a local/demo signed-session mechanism; production identity-provider integration and revocation are not implemented. Citation checks validate IDs and scope, not semantic entailment.

## Release verification

After the dedicated hosted database is available, apply migrations and seed, verify the restricted role, configure sensitive runtime variables, and build a preview. Check the complete frontend/API/database/citation/review flow before promotion and domain attachment. A health endpoint alone is insufficient. `.vercelignore` excludes local environments, runtimes, tests, evaluation answers, and administration scripts. Do not provision paid resources or change root-domain DNS.

## Current primary documentation

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/services
- https://vite.dev/guide/static-deploy.html

Consult current documentation again when selecting the exact implementation and deployment configuration.
