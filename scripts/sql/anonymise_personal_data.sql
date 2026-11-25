-- Remove the personal data that the prod → preprod sync copies
-- (.github/workflows/sync_databases.yml). Run against preprod only.

BEGIN;

TRUNCATE django_session;

-- Contact form submissions: names, emails and messages of visitors
TRUNCATE wagtailforms_formsubmission;

COMMIT;
