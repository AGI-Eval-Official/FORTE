#!/usr/bin/env bash
# Install the Anthropic general-purpose office skills (docx / pptx / xlsx / pdf)
# into ./data/extra_skills/, where the runner picks them up automatically and
# stages them into every agent container's ~/.openclaw/skills alongside each
# task's profession-specific skills.
#
# Usage:
#   bash scripts/install-anthropic-skills.sh           # docx pptx xlsx pdf (default)
#   SKILLS="docx xlsx" bash scripts/install-anthropic-skills.sh
#   ANTHROPIC_SKILLS_REF=v1.2.3 bash scripts/install-anthropic-skills.sh   # pin a tag

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
DEST="${ROOT}/data/extra_skills"
SKILLS="${SKILLS:-docx pptx xlsx pdf}"
REPO="${ANTHROPIC_SKILLS_REPO:-https://github.com/anthropics/skills.git}"
REF="${ANTHROPIC_SKILLS_REF:-main}"

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo ">>> Cloning ${REPO} @ ${REF} (shallow)"
git clone --depth 1 --branch "${REF}" "${REPO}" "${TMP}/skills" >/dev/null 2>&1 \
  || git clone "${REPO}" "${TMP}/skills" >/dev/null   # tags need full clone

mkdir -p "${DEST}"

for s in ${SKILLS}; do
  src="${TMP}/skills/skills/${s}"
  dst="${DEST}/${s}"
  if [ ! -d "${src}" ]; then
    echo "    skip: ${s} not found in upstream"
    continue
  fi
  echo ">>> ${s}"
  rm -rf "${dst}"
  cp -R "${src}" "${dst}"
done

echo ""
echo "Installed into ${DEST}:"
ls -la "${DEST}"
echo ""
echo "These will be auto-staged into every agent container's ~/.openclaw/skills/"
echo "on the next \`bash scripts/run.sh\`."
