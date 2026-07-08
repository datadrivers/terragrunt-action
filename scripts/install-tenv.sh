#!/usr/bin/env bash
# install-tenv.sh
# Installer for tenv - expects version to be pre-resolved
set -euo pipefail

# Version should be passed in, already resolved (not "latest")
TENV_VERSION="${INPUT_TENV_VERSION:-}"
[[ -z "$TENV_VERSION" ]] && { echo "ERROR: TENV_VERSION not provided" >&2; exit 1; }

echo "Installing tenv version: $TENV_VERSION"
ARCH="$(uname -m)"

# Use cached location for files (allow override via env var)
CACHE_DIR="${TENV_INSTALLER_CACHE_DIR:-${HOME}/.cache/tenv-installer}"
mkdir -p "${CACHE_DIR}"

TMP_DIR=$(mktemp -d)
# Ensure tmp dir is deleted
trap 'rm -rf "$TMP_DIR"' EXIT

decode_base64() {
  local input="$1"
  local output="$2"
  if command -v base64 >/dev/null 2>&1; then
    if base64 --decode < /dev/null >/dev/null 2>&1; then
      base64 --decode < "$input" > "$output"
      return 0
    elif base64 -d < /dev/null >/dev/null 2>&1; then
      base64 -d < "$input" > "$output"
      return 0
    elif base64 -D < /dev/null >/dev/null 2>&1; then
      base64 -D < "$input" > "$output"
      return 0
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import base64, sys; sys.stdout.buffer.write(base64.b64decode(open(sys.argv[1], 'rb').read()))" "$input" > "$output"
    return 0
  elif command -v python >/dev/null 2>&1; then
    python -c "import base64, sys; sys.stdout.buffer.write(base64.b64decode(open(sys.argv[1], 'rb').read()))" "$input" > "$output"
    return 0
  fi
  echo "ERROR: Neither base64 nor python is available to decode base64 files." >&2
  return 1
}

verify_openssl() {
  local artifact_path="$1"
  local sig_path="$2"
  local pem_path="$3"

  local decoded_sig="${TMP_DIR}/openssl_sig.bin"
  local decoded_cert="${TMP_DIR}/openssl_cert.pem"
  local public_key="${TMP_DIR}/openssl_public.pem"

  decode_base64 "$sig_path" "$decoded_sig" || return 1
  decode_base64 "$pem_path" "$decoded_cert" || return 1

  if ! openssl x509 -pubkey -noout -in "$decoded_cert" > "$public_key" 2>/dev/null; then
    echo "ERROR: Failed to extract public key from certificate $pem_path" >&2
    return 1
  fi

  if ! openssl dgst -sha256 -verify "$public_key" -signature "$decoded_sig" "$artifact_path"; then
    echo "ERROR: OpenSSL signature verification failed for $artifact_path" >&2
    return 1
  fi
  return 0
}

OS="$(uname -s)"
case "$OS" in
  Linux) OS_TAR="Linux" ;;
  Darwin) OS_TAR="Darwin" ;;
  *) OS_TAR="$OS" ;;
esac

case "$ARCH" in
  x86_64|amd64) ARCH_TAR="x86_64" ;;
  aarch64|arm64) ARCH_TAR="arm64" ;;
  *) ARCH_TAR="$ARCH" ;;
esac

EXT="tar.gz"
if [[ "$OS" == *"Windows"* || "$OS" == *"MINGW"* || "$OS" == *"MSYS"* ]]; then
  EXT="zip"
fi

TAR_FILENAME="tenv_${TENV_VERSION}_${OS_TAR}_${ARCH_TAR}.${EXT}"

download_file() {
  local filename="$1"
  local dest_path="${CACHE_DIR}/${filename}"
  if [[ -f "$dest_path" ]]; then
    echo "Using cached file: ${dest_path}"
  else
    echo "Downloading ${filename}..."
    local download_url="https://github.com/tofuutils/tenv/releases/download/${TENV_VERSION}/${filename}"
    local status
    status=$(curl --retry 3 -sSL -w '%{http_code}' -o "$dest_path" "$download_url" || echo "000")
    if ! [[ "$status" =~ ^2 ]]; then
      echo "Download of ${filename} failed with HTTP status ${status}" >&2
      return 1
    fi
  fi
  return 0
}

download_file "tenv_${TENV_VERSION}_checksums.txt" || exit 1
download_file "${TAR_FILENAME}" || exit 1

if ! command -v openssl >/dev/null 2>&1; then
  echo "ERROR: openssl is not installed but signature verification is required." >&2
  exit 1
fi

download_file "tenv_${TENV_VERSION}_checksums.txt.sig" || exit 1
download_file "tenv_${TENV_VERSION}_checksums.txt.pem" || exit 1
download_file "${TAR_FILENAME}.sig" || exit 1
download_file "${TAR_FILENAME}.pem" || exit 1

echo "Verifying signatures with openssl..."
verify_openssl "${CACHE_DIR}/tenv_${TENV_VERSION}_checksums.txt" \
               "${CACHE_DIR}/tenv_${TENV_VERSION}_checksums.txt.sig" \
               "${CACHE_DIR}/tenv_${TENV_VERSION}_checksums.txt.pem" || exit 1

verify_openssl "${CACHE_DIR}/${TAR_FILENAME}" \
               "${CACHE_DIR}/${TAR_FILENAME}.sig" \
               "${CACHE_DIR}/${TAR_FILENAME}.pem" || exit 1

echo "OpenSSL signature verification succeeded!"

SHASUM_CMD=""
if command -v shasum >/dev/null 2>&1; then
  SHASUM_CMD="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
  SHASUM_CMD="sha256sum"
fi

if [[ -n "$SHASUM_CMD" ]]; then
  echo "Verifying checksums..."
  (
    cd "$CACHE_DIR"
    if ! $SHASUM_CMD -c "tenv_${TENV_VERSION}_checksums.txt" --ignore-missing >/dev/null 2>&1; then
      # Fallback for systems/versions of shasum without --ignore-missing support
      expected_sha=$(grep "${TAR_FILENAME}" "tenv_${TENV_VERSION}_checksums.txt" | awk '{print $1}')
      if [[ -n "$expected_sha" ]]; then
        actual_sha=$($SHASUM_CMD "${TAR_FILENAME}" | awk '{print $1}')
        if [[ "$expected_sha" != "$actual_sha" ]]; then
          echo "Checksum verification failed for ${TAR_FILENAME}!" >&2
          exit 1
        fi
      else
        echo "Warning: ${TAR_FILENAME} not found in checksums file." >&2
      fi
    fi
  )
else
  echo "Warning: shasum/sha256sum not found, skipping checksum verification" >&2
fi

find_writable_path() {
  local IFS=':'
  for dir in $PATH; do
    [[ -z "$dir" ]] && continue
    if [[ -d "$dir" && -w "$dir" ]]; then
      if [[ "$dir" != "." && "$dir" != ".." ]]; then
        echo "$dir"
        return 0
      fi
    fi
  done
  return 1
}

INSTALL_DIR=$(find_writable_path || true)
if [[ -z "$INSTALL_DIR" ]]; then
  echo "ERROR: No writable directory found in PATH: $PATH" >&2
  exit 1
fi
echo "Installing tenv to $INSTALL_DIR..."

echo "Extracting ${TAR_FILENAME}..."
if [[ "$EXT" == "zip" ]]; then
  unzip -q "${CACHE_DIR}/${TAR_FILENAME}" -d "$TMP_DIR"
else
  tar -xzf "${CACHE_DIR}/${TAR_FILENAME}" -C "$TMP_DIR"
fi

# Copy executables
for file in "$TMP_DIR"/*; do
  if [[ -f "$file" && -x "$file" ]]; then
    cp -f "$file" "$INSTALL_DIR/"
  fi
done

# Confirm installation
tenv --version
