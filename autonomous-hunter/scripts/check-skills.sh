#!/usr/bin/env bash
# check-skills.sh - skill integrity lint (bash port of check-skills.ps1)
# Validates: (1) folder == frontmatter name, (2) description present + <=300 chars,
# (3) every "Composes with" name exists as a folder, (4) zero retired-name hits.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIRS=("$ROOT/.opencode/skills")
GLOBAL_SKILLS="$HOME/.config/opencode/skills"
[ -d "$GLOBAL_SKILLS" ] && SKILL_DIRS+=("$GLOBAL_SKILLS")
RETIRED='lead-intake-rules|hotspot-mapper|dead-lead-residue|realistic-attacker-constraint'
fail=0
all_folders=""
count=0

for d in "${SKILL_DIRS[@]}"; do
  [ -d "$d" ] || continue
  for s in "$d"/*/; do
    name="$(basename "$s")"
    all_folders="$all_folders $name"
    count=$((count+1))
    skillfile="$s/SKILL.md"
    if [ ! -f "$skillfile" ]; then echo "MISSING SKILL.md in $name"; fail=$((fail+1)); continue; fi
    fm="$(awk 'NR==1 && $0=="---"{f=1;next} f&&$0=="---"{exit} f{print}' "$skillfile")"
    if [ -z "$fm" ]; then echo "$name: no frontmatter"; fail=$((fail+1)); continue; fi
    fname="$(echo "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -1)"
    fdesc="$(echo "$fm" | sed -n 's/^description:[[:space:]]*//p' | head -1)"
    [ "$fname" = "$name" ] || { echo "$name: frontmatter name '$fname' != folder"; fail=$((fail+1)); }
    if [ -z "$fdesc" ]; then echo "$name: missing description"; fail=$((fail+1));
    elif [ "${#fdesc}" -gt 300 ]; then echo "$name: description ${#fdesc} chars > 300"; fail=$((fail+1)); fi
    comp="$(grep -m1 '^\*\*Composes with:\*\*' "$skillfile" || true)"
    if [ -z "$comp" ]; then echo "$name: missing Composes with footer"; fail=$((fail+1)); continue; fi
    line="${comp#**Composes with:**}"
    IFS=',' read -ra toks <<< "$line"
    for tok in "${toks[@]}"; do
      n="$(echo "$tok" | sed 's/^[[:space:]]*//; s/[[:space:]]*(.*//; s/[[:space:]]*$//')"
      [ -z "$n" ] && continue
      case " $all_folders " in
        *" $n "*) ;;
        *) echo "$name: Composes-with '$n' has no folder"; fail=$((fail+1)) ;;
      esac
    done
  done
done

# retired names in live config surfaces
targets=("$ROOT/AGENTS.md")
for d in "${SKILL_DIRS[@]}"; do
  [ -d "$d" ] || continue
  while IFS= read -r f; do targets+=("$f"); done < <(find "$d" -name '*.md' -type f)
done
[ -d "$ROOT/hunt" ] && while IFS= read -r f; do targets+=("$f"); done < <(find "$ROOT/hunt" -maxdepth 1 -name '*.md' -type f)
for f in "${targets[@]}"; do
  [ -f "$f" ] || continue
  while IFS= read -r h; do
    case "$h" in
      *'**Renamed from:**'*) ;;
      *) echo "RETIRED NAME in $f: $h"; fail=$((fail+1)) ;;
    esac
  done < <(grep -nE "$RETIRED" "$f" 2>/dev/null || true)
done

if [ "$fail" -eq 0 ]; then
  echo "OK: $count skills validated - folder==name, descriptions in budget, Composes-with resolve, no retired names."
  exit 0
else
  echo "FAIL ($fail issues)"
  exit 1
fi
