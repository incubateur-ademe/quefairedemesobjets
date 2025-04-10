DUMP_FILE=/home/me/Downloads/20250410002559_quefairedem_5084/20250410002559_quefairedem_5084.pgsql
DATABASE_URL=postgres://qfdmo:qfdmo@localhost:6543/qfdmo # pragma: allowlist secret

for table in $(psql "${DATABASE_URL}" -t -c "SELECT \"tablename\" FROM pg_tables WHERE schemaname='public'"); do
     psql "${DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;"
done
pg_restore -d "${DATABASE_URL}" --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}"
