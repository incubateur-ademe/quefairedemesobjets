#!/usr/bin/env bash
# Run with: bash .github/scripts/ci_changed_areas_test.sh
set -u
script="$(dirname "$0")/ci_changed_areas.sh"
failures=0

check() {
  local files=$1 expected=$2 actual
  actual=$(printf '%b' "$files" | bash "$script" | grep '=true' | cut -d= -f1 | sort | xargs)
  if [ "$actual" != "$expected" ]; then
    echo "FAIL [$files]: expected '$expected', got '$actual'"
    failures=$((failures + 1))
  fi
}

ALL="frontend infra python revue"
check "docs/reference/x.md\n" ""
check "README.md\nwebapp/README.md\n" ""
check "uv.lock\n" "python"
check "pyproject.toml\n" "python"
check "ml_deduplication/uv.lock\n" "python"
check "data-platform/dags/x.py\n" "python"
check "webapp/qfdmo/models.py\n" "python"
check "webapp/templates/x.html\n" "python"
check "package-lock.json\n" "frontend revue"
check "webapp/package.json\nwebapp/revue-front/package.json\npackage-lock.json\n" "frontend revue"
check "webapp/static/to_compile/x.ts\n" "frontend"
check "webapp/jest.config.ts\n" "frontend"
check "webapp/revue-front/src/x.tsx\n" "revue"
check "infrastructure/modules/x.tf\n" "infra"
check "webapp/qfdmo/models.py\nwebapp/static/to_compile/x.ts\n" "frontend python"
check ".github/workflows/ci.yml\n" "$ALL"
check ".github/actions/setup-backend/action.yml\n" "$ALL"
check "Makefile\n" "$ALL"
check "some/unknown/file\n" "$ALL"
check "docs/x.md\nsome/unknown/file\n" "$ALL"
check "" "$ALL"

[ "$failures" -eq 0 ] && echo "all passed"
exit "$failures"
