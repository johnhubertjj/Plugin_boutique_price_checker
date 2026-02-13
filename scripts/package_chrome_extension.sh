#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT_DIR="$ROOT_DIR/chrome_extension"
MANIFEST_PATH="$EXT_DIR/manifest.json"
OUTPUT_DIR="$ROOT_DIR/dist/chrome_extension"

if [[ ! -f "$MANIFEST_PATH" ]]; then
  echo "manifest.json not found at $MANIFEST_PATH" >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip is required but not installed" >&2
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  EXT_NAME="$(jq -r '.name // "chrome-extension"' "$MANIFEST_PATH")"
  EXT_VERSION="$(jq -r '.version // empty' "$MANIFEST_PATH")"
else
  EXT_NAME="$(grep -E '"name"' "$MANIFEST_PATH" | head -n 1 | sed -E 's/.*"name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
  EXT_VERSION="$(grep -E '"version"' "$MANIFEST_PATH" | head -n 1 | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
fi

if [[ -z "$EXT_VERSION" ]]; then
  echo "Could not determine extension version from manifest" >&2
  exit 1
fi

SAFE_NAME="$(echo "$EXT_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
ARCHIVE_NAME="${SAFE_NAME}-${EXT_VERSION}.zip"
ARCHIVE_PATH="$OUTPUT_DIR/$ARCHIVE_NAME"

mkdir -p "$OUTPUT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

rsync -a --delete \
  --exclude '.DS_Store' \
  --exclude 'README.md' \
  --exclude 'PRIVACY_POLICY.md' \
  "$EXT_DIR/" "$TMP_DIR/"

required_files=(
  "manifest.json"
  "popup.html"
  "popup.js"
  "background.js"
  "options.html"
  "options.js"
)

for rel_path in "${required_files[@]}"; do
  if [[ ! -f "$TMP_DIR/$rel_path" ]]; then
    echo "Required file missing from package source: $rel_path" >&2
    exit 1
  fi
done

(
  cd "$TMP_DIR"
  zip -X -r "$ARCHIVE_PATH" . >/dev/null
)

SHA256="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"

cat <<OUT
Chrome extension package created:
- Archive: $ARCHIVE_PATH
- SHA256:  $SHA256
OUT
