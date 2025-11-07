#!/usr/bin/env bash
# install-tenv.sh
# Hardened installer for tenv with robust latest version resolution.
set -euo pipefail

INPUT_TENV_VERSION="${INPUT_TENV_VERSION:-latest}"
INPUT_GITHUB_TOKEN="${INPUT_GITHUB_TOKEN:-}" # optional

resolve_tenv_latest() {
  local api_base="https://api.github.com/repos/tofuutils/tenv"
  # Always initialize array to avoid unbound variable errors with set -u
  local auth_header=()
  if [[ -n "$INPUT_GITHUB_TOKEN" ]]; then
    auth_header=( -H "Authorization: Bearer $INPUT_GITHUB_TOKEN" )
  fi
  local resp body code ver
  # Try releases/latest
  resp="$(curl -sS -w '\n%{http_code}' -L "${api_base}/releases/latest" ${auth_header:+"${auth_header[@]}"})" || resp=""
  code="${resp##*$'\n'}"
  body="${resp%$'\n'$code}"
  if [[ "$code" != 200 || -z "$body" ]]; then
    echo "WARN: releases/latest returned HTTP $code" >&2
    # Fallback to tags endpoint (fast)
    resp="$(curl -sS -w '\n%{http_code}' -L "${api_base}/tags?per_page=1" ${auth_header:+"${auth_header[@]}"})" || resp=""
    code="${resp##*$'\n'}"; body="${resp%$'\n'$code}"
    [[ "$code" != 200 || -z "$body" ]] && { echo "ERROR: tags fallback failed (HTTP $code)" >&2; return 1; }
  fi
  ver=""
  if command -v jq >/dev/null 2>&1; then
    ver="$(printf '%s' "$body" | jq -r '.tag_name // .name // .[0].name // empty')"
  fi
  if [[ -z "$ver" ]]; then
    ver="$(printf '%s' "$body" | awk 'match($0,/"tag_name"[[:space:]]*:[[:space:]]*"([^"]+)"/,a){print a[1]; exit} match($0,/"name"[[:space:]]*:[[:space:]]*"([^"]+)"/,b){print b[1]; exit}')"
  fi
  [[ -z "$ver" ]] && { echo "ERROR: Unable to parse version from response" >&2; return 1; }
  [[ $ver != v* ]] && ver="v$ver"
  printf '%s' "$ver"
}

if [[ "$INPUT_TENV_VERSION" == "latest" ]]; then
  echo "Resolving latest tenv release via GitHub API";
  TENV_VERSION="$(resolve_tenv_latest)" || { echo "Failed to determine latest tenv version" >&2; exit 1; }
else
  TENV_VERSION="$INPUT_TENV_VERSION"
  [[ $TENV_VERSION != v* ]] && TENV_VERSION="v$TENV_VERSION"
fi

echo "Using tenv version: $TENV_VERSION"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) ARCH_DEB="amd64" ;;
  aarch64|arm64) ARCH_DEB="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
 esac

DEB_FILE="tenv_${TENV_VERSION}_${ARCH_DEB}.deb"
DOWNLOAD_URL="https://github.com/tofuutils/tenv/releases/download/${TENV_VERSION}/${DEB_FILE}"

bin_status=$(curl --retry 3 -sSL -w '%{http_code}' -o "${DEB_FILE}" "${DOWNLOAD_URL}" || echo "000")
if ! [[ "$bin_status" =~ ^2 ]]; then
  echo "Download failed with HTTP status ${bin_status}" >&2
  exit 1
fi

if command -v sudo >/dev/null 2>&1; then
  sudo dpkg -i "${DEB_FILE}"
else
  dpkg -i "${DEB_FILE}"
fi
