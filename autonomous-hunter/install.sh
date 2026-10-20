#!/usr/bin/env bash
# install.sh - install Autonomous Hunter into a target (macOS/Linux)
# Usage:
#   ./install.sh                      # install into current directory (project mode)
#   ./install.sh /path/to/proj        # install into a specific project
#   ./install.sh --global             # install into ~/.config/opencode
#   ./install.sh /path/to/proj --claude   # also lay down Claude Code skill stubs
#   ./install.sh --force              # overwrite existing skill folders
set -euo pipefail
PKG="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$PKG/.opencode/skills"
[ -d "$SKILLS_SRC" ] || { echo "skills not found at $SKILLS_SRC"; exit 1; }

TARGET=""
GLOBAL=0
CLAUDE=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --global) GLOBAL=1 ;;
    --claude) CLAUDE=1 ;;
    --force) FORCE=1 ;;
    *) TARGET="$arg" ;;
  esac
done

if [ "$GLOBAL" = 1 ]; then
  DEST_ROOT="$HOME/.config/opencode"
  SKILLS_DST="$DEST_ROOT/skills"
  AGENTS_DST="$DEST_ROOT/AGENTS.md"
else
  [ -z "$TARGET" ] && TARGET="$(pwd)"
  DEST_ROOT="$TARGET"
  SKILLS_DST="$DEST_ROOT/.opencode/skills"
  AGENTS_DST="$DEST_ROOT/AGENTS.md"
fi

mkdir -p "$SKILLS_DST"
copied=0
for s in "$SKILLS_SRC"/*/; do
  name="$(basename "$s")"
  dst="$SKILLS_DST/$name"
  if [ -d "$dst" ] && [ "$FORCE" != 1 ]; then
    echo "SKIP  $name (exists; use --force to overwrite)"
    continue
  fi
  rm -rf "$dst"
  cp -R "$s" "$dst"
  echo "COPY  $name"
  copied=$((copied+1))
done

if [ ! -f "$AGENTS_DST" ] || [ "$FORCE" = 1 ]; then
  cp -f "$PKG/AGENTS.md" "$AGENTS_DST"
  echo "COPY  AGENTS.md -> $AGENTS_DST"
else
  echo "SKIP  AGENTS.md (exists; use --force to overwrite)"
fi

if [ "$GLOBAL" != 1 ]; then
  OC_DST="$DEST_ROOT/opencode.json"
  if [ ! -f "$OC_DST" ]; then
    cp -f "$PKG/opencode.json" "$OC_DST"
    echo "COPY  opencode.json -> $OC_DST (edit providers/models to taste)"
  else
    echo "SKIP  opencode.json (exists; merge 'instructions' and 'references' by hand)"
  fi
fi

if [ "$CLAUDE" = 1 ]; then
  CLAUDE_SKILLS="$DEST_ROOT/.claude/skills"
  mkdir -p "$CLAUDE_SKILLS"
  for s in "$SKILLS_SRC"/*/; do
    name="$(basename "$s")"
    [ -f "$s/SKILL.md" ] || continue
    mkdir -p "$CLAUDE_SKILLS/$name"
    cp -f "$s/SKILL.md" "$CLAUDE_SKILLS/$name/SKILL.md"
  done
  echo "COPY  Claude Code stubs -> $CLAUDE_SKILLS"
fi

echo ""
echo "Installed $copied skills + AGENTS.md into $DEST_ROOT"
echo "Verify:  $PKG/scripts/check-skills.sh"
echo "Start:   open opencode in $DEST_ROOT and ask for an autonomous hunt"
