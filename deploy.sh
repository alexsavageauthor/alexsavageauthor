#!/usr/bin/env bash
#
# One-command deploy for the Alex Savage site.
#
#   ./deploy.sh "what changed"     # commits everything + pushes to main
#   ./deploy.sh                    # uses a dated default message
#
# Pushing to main triggers GitHub Pages to rebuild alexsavageauthor.com.
#
set -euo pipefail
cd "$(dirname "$0")"

# Clear any stale lock left by an interrupted git process.
rm -f .git/index.lock 2>/dev/null || true

MSG="${1:-Site update $(date +%Y-%m-%d)}"

# Validate before pushing (same gate the CI runs) — abort if it fails.
if command -v python3 >/dev/null 2>&1; then
  echo "→ Validating…"
  python3 .github/scripts/validate_site.py
fi

git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit — working tree is clean."
  exit 0
fi

git commit -m "$MSG"
git push origin main

echo
echo "✓ Pushed to main. alexsavageauthor.com rebuilds in ~1 minute."
echo "  Watch the build: https://github.com/alexsavageauthor/alexsavageauthor/actions"
