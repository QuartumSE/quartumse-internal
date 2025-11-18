#!/bin/bash
# Sync SDK changes from QuartumSE-internal (here) to QuartumSE (public)
#
# Usage: ./sync-to-public.sh

set -e

INTERNAL="."
PUBLIC="../QuartumSE"

echo "🔄 Syncing SDK from QuartumSE-internal to QuartumSE (public)..."

# Check that public repo exists
if [ ! -d "$PUBLIC" ]; then
    echo "❌ Error: Public repo not found at $PUBLIC"
    echo "Expected structure:"
    echo "  Projects/"
    echo "    ├── QuartumSE-internal/  (you are here)"
    echo "    └── QuartumSE/           (public repo)"
    exit 1
fi

# Sync SDK source
echo "  ├─ Copying src/quartumse/..."
rsync -av --delete "$INTERNAL/src/quartumse/" "$PUBLIC/src/quartumse/"

# Sync tests
echo "  ├─ Copying tests/..."
rsync -av --delete "$INTERNAL/tests/" "$PUBLIC/tests/"

# Sync public documentation only
echo "  ├─ Copying public docs..."
rsync -av --delete "$INTERNAL/docs/api/" "$PUBLIC/docs/api/"
rsync -av --delete "$INTERNAL/docs/tutorials/" "$PUBLIC/docs/tutorials/"
rsync -av --delete "$INTERNAL/docs/how-to/" "$PUBLIC/docs/how-to/"
rsync -av --delete "$INTERNAL/docs/explanation/" "$PUBLIC/docs/explanation/"
rsync -av --delete "$INTERNAL/docs/community/" "$PUBLIC/docs/community/"
rsync -av --delete "$INTERNAL/docs/reference/" "$PUBLIC/docs/reference/"

# Sync root config files (but not READMEs - they're different)
echo "  ├─ Copying pyproject.toml..."
cp "$INTERNAL/pyproject.toml" "$PUBLIC/pyproject.toml"

echo "  ├─ Copying LICENSE..."
cp "$INTERNAL/LICENSE" "$PUBLIC/LICENSE"

echo "  ├─ Copying CHANGELOG.md..."
cp "$INTERNAL/CHANGELOG.md" "$PUBLIC/CHANGELOG.md"

echo "  └─ Copying .gitignore..."
cp "$INTERNAL/.gitignore" "$PUBLIC/.gitignore"

echo ""
echo "✅ Sync complete!"
echo ""
echo "Next steps:"
echo "  cd $PUBLIC"
echo "  git status          # Review changes"
echo "  pytest tests/       # Test"
echo "  git add ."
echo "  git commit -m 'Sync: <description>'"
echo "  git push"
