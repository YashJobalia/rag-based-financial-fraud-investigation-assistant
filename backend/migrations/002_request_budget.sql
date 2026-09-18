CREATE TABLE request_budgets (
 tenant_id text NOT NULL,
 actor text NOT NULL,
 minute timestamptz NOT NULL,
 requests integer NOT NULL DEFAULT 1 CHECK(requests>0),
 PRIMARY KEY(tenant_id,actor,minute)
);
ALTER TABLE request_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_budgets FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON request_budgets
 USING(tenant_id=current_setting('app.tenant',true))
 WITH CHECK(tenant_id=current_setting('app.tenant',true));
GRANT SELECT,INSERT,UPDATE ON request_budgets TO ffia_app;
INSERT INTO schema_migrations(version) VALUES(2);
