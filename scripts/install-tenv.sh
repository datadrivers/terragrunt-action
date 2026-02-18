#!/usr/bin/env bash
# install-tenv.sh
# Installer for tenv - expects version to be pre-resolved
set -euo pipefail

# Version should be passed in, already resolved (not "latest")
TENV_VERSION="${INPUT_TENV_VERSION:-}"
[[ -z "$TENV_VERSION" ]] && { echo "ERROR: TENV_VERSION not provided" >&2; exit 1; }

echo "Installing tenv version: $TENV_VERSION"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) ARCH_DEB="amd64" ;;
  aarch64|arm64) ARCH_DEB="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
 esac

# Use cached location for .deb file (allow override via env var)
CACHE_DIR="${TENV_INSTALLER_CACHE_DIR:-${HOME}/.cache/tenv-installer}"
mkdir -p "${CACHE_DIR}"
DEB_FILENAME="tenv_${TENV_VERSION}_${ARCH_DEB}.deb"
DEB_FILE="${CACHE_DIR}/${DEB_FILENAME}"

# Download only if not already cached
if [[ -f "${DEB_FILE}" ]]; then
  echo "Using cached tenv installer: ${DEB_FILE}"
else
  echo "Downloading tenv ${TENV_VERSION} for ${ARCH_DEB}..."
  DOWNLOAD_URL="https://github.com/tofuutils/tenv/releases/download/${TENV_VERSION}/${DEB_FILENAME}"
  bin_status=$(curl --retry 3 -sSL -w '%{http_code}' -o "${DEB_FILE}" "${DOWNLOAD_URL}" || echo "000")
  if ! [[ "$bin_status" =~ ^2 ]]; then
    echo "Download failed with HTTP status ${bin_status}" >&2
    exit 1
  fi
  echo "Download complete"
fi

if command -v sudo >/dev/null 2>&1; then
  sudo dpkg -i "${DEB_FILE}"
else
  dpkg -i "${DEB_FILE}"
fi
