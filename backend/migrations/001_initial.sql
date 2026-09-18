CREATE TABLE IF NOT EXISTS schema_migrations(version integer PRIMARY KEY, applied_at timestamptz DEFAULT now());

CREATE TABLE memberships (
 tenant_id text NOT NULL, actor text NOT NULL, role text NOT NULL CHECK(role IN ('viewer','analyst')),
 PRIMARY KEY(tenant_id, actor)
);
CREATE TABLE accounts (
 tenant_id text NOT NULL, id text NOT NULL, display_name text NOT NULL,
 opened_at timestamptz NOT NULL, PRIMARY KEY(tenant_id,id)
);
CREATE TABLE cases (
 tenant_id text NOT NULL, id text NOT NULL, account_id text NOT NULL, title text NOT NULL,
 opened_at timestamptz NOT NULL, cutoff_at timestamptz NOT NULL,
 status text NOT NULL DEFAULT 'open', PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,account_id) REFERENCES accounts(tenant_id,id)
);
CREATE TABLE case_assignments (
 tenant_id text NOT NULL, case_id text NOT NULL, actor text NOT NULL,
 PRIMARY KEY(tenant_id,case_id,actor), FOREIGN KEY(tenant_id,case_id) REFERENCES cases(tenant_id,id)
);
CREATE TABLE events (
 tenant_id text NOT NULL, id text NOT NULL, account_id text NOT NULL,
 kind text NOT NULL, occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL,
 title text NOT NULL, description text NOT NULL, device_id text, recipient_id text,
 source text NOT NULL, PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,account_id) REFERENCES accounts(tenant_id,id)
);
CREATE TABLE transactions (
 tenant_id text NOT NULL, id text NOT NULL, account_id text NOT NULL,
 recipient_id text NOT NULL, amount_minor bigint NOT NULL CHECK(amount_minor>0),
 currency text NOT NULL CHECK(currency ~ '^[A-Z]{3}$'), status text NOT NULL,
 occurred_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,account_id) REFERENCES accounts(tenant_id,id)
);
CREATE TABLE alerts (
 tenant_id text NOT NULL, id text NOT NULL, case_id text NOT NULL,
 rule_id text NOT NULL, rule_version text NOT NULL, triggered_at timestamptz NOT NULL,
 description text NOT NULL, evidence_ids jsonb NOT NULL,
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,case_id) REFERENCES cases(tenant_id,id)
);
CREATE TABLE chunks (
 tenant_id text NOT NULL, id text NOT NULL, document_id text NOT NULL,
 title text NOT NULL, kind text NOT NULL CHECK(kind IN ('procedure','historical_report')),
 version text NOT NULL, section text NOT NULL, passage text NOT NULL,
 content_hash text NOT NULL, published_at timestamptz NOT NULL, ingested_at timestamptz NOT NULL,
 access_group text NOT NULL CHECK(access_group IN ('demo','restricted')),
 source_uri text NOT NULL, synthetic boolean NOT NULL DEFAULT true CHECK(synthetic),
 search_vector tsvector GENERATED ALWAYS AS
 (setweight(to_tsvector('english', title),'A') || setweight(to_tsvector('english',passage),'B')) STORED,
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,document_id,version,section)
);
CREATE INDEX chunks_search ON chunks USING gin(search_vector);
CREATE INDEX events_account_time ON events(tenant_id,account_id,occurred_at);
CREATE INDEX transactions_account_time ON transactions(tenant_id,account_id,occurred_at);
CREATE TABLE retrieval_runs (
 id text PRIMARY KEY, tenant_id text NOT NULL, actor text NOT NULL, case_id text NOT NULL,
 mode text NOT NULL, query text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 duration_ms float NOT NULL, result_ids jsonb NOT NULL, corpus_hash text NOT NULL
);
CREATE TABLE briefs (
 id text PRIMARY KEY, tenant_id text NOT NULL, case_id text NOT NULL, actor text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), mode text NOT NULL, model text,
 content jsonb NOT NULL, evidence_ids jsonb NOT NULL, retrieval_run_id text NOT NULL,
 prompt_version text NOT NULL, duration_ms float NOT NULL, usage jsonb NOT NULL,
 FOREIGN KEY(tenant_id,case_id) REFERENCES cases(tenant_id,id)
);
CREATE TABLE reviews (
 id text PRIMARY KEY, tenant_id text NOT NULL, case_id text NOT NULL, actor text NOT NULL,
 brief_id text NOT NULL REFERENCES briefs(id), disposition text NOT NULL,
 notes text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(tenant_id,case_id) REFERENCES cases(tenant_id,id)
);
CREATE TABLE generation_attempts (
 id text PRIMARY KEY, tenant_id text NOT NULL, actor text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE audit_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, tenant_id text NOT NULL,
 actor text NOT NULL, case_id text, action text NOT NULL, occurred_at timestamptz DEFAULT now()
);

DO $$
DECLARE t text;
BEGIN
 FOREACH t IN ARRAY ARRAY['memberships','accounts','cases','case_assignments','events','transactions',
 'alerts','chunks','retrieval_runs','briefs','reviews','generation_attempts','audit_events'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_isolation ON %I USING (tenant_id = current_setting(''app.tenant'', true)) WITH CHECK (tenant_id = current_setting(''app.tenant'', true))',t);
 END LOOP;
END $$;

-- The runtime role cannot migrate, seed, change evidence, or bypass RLS.
GRANT USAGE ON SCHEMA public TO ffia_app;
GRANT SELECT ON memberships,accounts,cases,case_assignments,events,transactions,alerts,chunks TO ffia_app;
GRANT SELECT,INSERT ON retrieval_runs,briefs,reviews,generation_attempts,audit_events TO ffia_app;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO ffia_app;
INSERT INTO schema_migrations(version) VALUES(1);
