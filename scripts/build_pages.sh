#!/usr/bin/env bash
# Assemble GitHub Pages site from web/ + docs/*.md (pandoc → HTML).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="${ROOT}/_site"
DOCS="${ROOT}/docs"
WEB="${ROOT}/web"
TEMPLATE="${ROOT}/web/_pandoc.html"

rm -rf "$SITE"
mkdir -p "$SITE"
cp -r "$WEB"/* "$SITE"/
rm -f "$SITE/_pandoc.html"
touch "$SITE/.nojekyll"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc is required to build Pages HTML" >&2
  exit 1
fi

# Rewrite .md links to .html for in-site navigation after pandoc.
fix_md_links() {
  python3 - "$1" <<'PY'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
# [label](foo.md) / [label](foo.md#anchor) → .html
text = re.sub(
    r"\]\((?!https?://|mailto:)([^)#]+)\.md(#[^)]*)?\)",
    lambda m: f"]({m.group(1)}.html{m.group(2) or ''})",
    text,
)
path.write_text(text)
PY
}

shopt -s nullglob
for md in "$DOCS"/*.md; do
  name="$(basename "$md" .md)"
  tmp="$(mktemp)"
  cp "$md" "$tmp"
  fix_md_links "$tmp"
  pandoc "$tmp" \
    --from gfm \
    --to html5 \
    --standalone \
    --template="$TEMPLATE" \
    --metadata title="$name" \
    -o "$SITE/${name}.html"
  rm -f "$tmp"
  echo "wrote ${name}.html"
done

echo "Pages site in $SITE"
