#!/usr/bin/env bash
# Generate trusted local TLS certificates (mkcert) for Relay Compose HTTPS.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${ROOT_DIR}/infra/caddy/.certs"
CERT_FILE="${CERT_DIR}/relay-local.pem"
KEY_FILE="${CERT_DIR}/relay-local-key.pem"

HOSTS=(
  acme-relay.local
  api.acme-relay.local
  auth.acme-relay.local
  glitchtip.local
  langfuse.local
  grafana.local
)
HOSTS_LINE="127.0.0.1 acme-relay.local api.acme-relay.local auth.acme-relay.local glitchtip.local langfuse.local grafana.local"

require_mkcert() {
  if ! command -v mkcert >/dev/null 2>&1; then
    printf '[tls] mkcert is required.\n' >&2
    printf '[tls] Install: brew install mkcert nss   # or see https://github.com/FiloSottile/mkcert\n' >&2
    exit 1
  fi
}

ensure_hosts() {
  if grep -q 'acme-relay.local' /etc/hosts 2>/dev/null; then
    printf '[tls] /etc/hosts already contains acme-relay.local\n'
    return 0
  fi
  printf '[tls] Adding local hostnames to /etc/hosts (sudo)…\n'
  if command -v sudo >/dev/null 2>&1; then
    printf '%s\n' "${HOSTS_LINE}" | sudo tee -a /etc/hosts >/dev/null
  else
    printf '[tls] Add this line to /etc/hosts manually:\n%s\n' "${HOSTS_LINE}" >&2
    return 1
  fi
}

generate_certs() {
  mkdir -p "${CERT_DIR}"
  printf '[tls] Installing local CA into system trust store (mkcert -install)…\n'
  mkcert -install
  printf '[tls] Generating certificate for: %s\n' "${HOSTS[*]}"
  mkcert -cert-file "${CERT_FILE}" -key-file "${KEY_FILE}" "${HOSTS[@]}"
  chmod 644 "${CERT_FILE}"
  chmod 600 "${KEY_FILE}"
  printf '[tls] Wrote %s and %s\n' "${CERT_FILE}" "${KEY_FILE}"
}

print_urls() {
  cat <<EOF

[tls] Ready. After \`make tls-up\`:

  Command Desk  https://acme-relay.local
  API docs      https://api.acme-relay.local/docs
  Keycloak      https://auth.acme-relay.local
  GlitchTip     https://glitchtip.local
  Langfuse      https://langfuse.local
  Grafana       https://grafana.local

EOF
}

require_mkcert
ensure_hosts || true
generate_certs
print_urls
