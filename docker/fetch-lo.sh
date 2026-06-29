#!/usr/bin/env bash
# Pre-stage LibreOffice 26.2.4 deb tarballs into docker/lo-pkgs/ so the image
# build does not depend on in-build network egress.
#
# The default LO_MIRROR points to The Document Foundation's canonical download
# host. If your network reaches a regional mirror faster, override it for your
# local fetch:
#   LO_MIRROR=https://your-mirror.example/tdf/libreoffice/stable docker/fetch-lo.sh
#
# Usage:
#   docker/fetch-lo.sh            # fetch for the host arch (arm64 on Apple Silicon)
#   ARCHES="aarch64 x86_64" docker/fetch-lo.sh   # fetch both for multi-arch
set -euo pipefail

LO_VERSION="${LO_VERSION:-26.2.4}"
LO_MIRROR="${LO_MIRROR:-https://download.documentfoundation.org/libreoffice/stable}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${HERE}/lo-pkgs"
mkdir -p "${DEST}"

# Default to the host arch; uname -m gives arm64/aarch64 or x86_64.
if [ -z "${ARCHES:-}" ]; then
  case "$(uname -m)" in
    arm64|aarch64) ARCHES="aarch64" ;;
    x86_64|amd64)  ARCHES="x86_64" ;;
    *) echo "unknown host arch $(uname -m); set ARCHES explicitly" >&2; exit 1 ;;
  esac
fi

for ARCH_DIR in ${ARCHES}; do
  case "${ARCH_DIR}" in
    aarch64) TAG=aarch64 ;;
    x86_64)  TAG=x86-64 ;;
    *) echo "unsupported arch ${ARCH_DIR}" >&2; exit 1 ;;
  esac
  BASE="${LO_MIRROR}/${LO_VERSION}/deb/${ARCH_DIR}"
  for F in \
    "LibreOffice_${LO_VERSION}_Linux_${TAG}_deb.tar.gz" \
    "LibreOffice_${LO_VERSION}_Linux_${TAG}_deb_langpack_zh-CN.tar.gz"; do
    echo ">>> ${F}"
    curl -fSL --http1.1 --retry 8 --retry-delay 5 --retry-all-errors -C - \
      -o "${DEST}/${F}" "${BASE}/${F}"
    gzip -t "${DEST}/${F}"
    echo "    ok: $(du -h "${DEST}/${F}" | cut -f1)"
  done
done

echo "staged into ${DEST}:"
ls -la "${DEST}"
