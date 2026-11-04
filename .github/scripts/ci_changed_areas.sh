#!/usr/bin/env bash
# Reads changed file paths on stdin, prints which CI areas must run.
# Anything unrecognised, and an empty list, runs everything.
set -eu

python=false frontend=false revue=false infra=false

run_everything() {
  python=true frontend=true revue=true infra=true
}

seen=false
while IFS= read -r file; do
  seen=true
  case "$file" in
    docs/* | *.md) ;;
    infrastructure/*) infra=true ;;
    package.json | package-lock.json | webapp/package.json)
      frontend=true revue=true
      ;;
    webapp/revue-front/*) revue=true ;;
    webapp/static/to_compile/* | webapp/*.config.* | webapp/tsconfig.json | webapp/.eslintrc.js | webapp/.parcelrc | webapp/.postcssrc | webapp/parcel-transformers/*)
      frontend=true
      ;;
    # webapp and data-platform import each other, so they are tested together.
    uv.lock | pyproject.toml | webapp/* | data-platform/* | ml_deduplication/*)
      python=true
      ;;
    *) run_everything ;;
  esac
done

[ "$seen" = true ] || run_everything

echo "python=$python"
echo "frontend=$frontend"
echo "revue=$revue"
echo "infra=$infra"
