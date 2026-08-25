-- DataGovOps v0.4 PostgreSQL institution-isolation reference.
-- Reference/deployment contract only. CI validation does not prove production isolation,
-- data confidentiality, regulatory compliance, or supervisory acceptance.

CREATE ROLE datagovops_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;

ALTER TABLE datagovops_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE datagovops_evidence FORCE ROW LEVEL SECURITY;

CREATE POLICY datagovops_evidence_institution_isolation
ON datagovops_evidence
USING (
  institution_id = current_setting('datagovops.institution_id', true)
)
WITH CHECK (
  institution_id = current_setting('datagovops.institution_id', true)
);

REVOKE ALL ON datagovops_evidence FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON datagovops_evidence TO datagovops_app;

-- Application transactions must set authenticated institution scope locally:
--   BEGIN;
--   SET LOCAL datagovops.institution_id = 'bank-a';
--   ... statements ...
--   COMMIT;
--
-- Production validation must separately prove:
-- * application role remains non-superuser and NOBYPASSRLS;
-- * FORCE ROW LEVEL SECURITY remains enabled;
-- * pooled connections cannot leak a previous institution setting;
-- * cross-institution SELECT/INSERT/UPDATE/DELETE fail closed;
-- * migration, backup/restore, maintenance and break-glass roles are separately governed.
