#!/usr/bin/env bash
# Sync elite-hacker skills from this repo into ~/.claude/skills/
# Each skill dir is copied top-level (Claude Code convention), replacing same-named dirs.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills"

for d in "$REPO"/skills/*/; do
    name="$(basename "$d")"
    rm -rf "$DEST/$name"
    cp -r "$d" "$DEST/$name"
done
echo "Synced $(ls "$REPO"/skills/ | wc -l) skills to $DEST"
