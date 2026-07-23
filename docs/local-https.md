# Local HTTPS via Caddy + mkcert (optional overlay)
#
# Prerequisites: mkcert (`brew install mkcert nss`)
#
# ```bash
# make tls-certs   # install CA, write certs, ensure /etc/hosts
# make tls-up      # compose up with docker-compose.tls.yml
# ```
#
# | Service | URL |
# |---------|-----|
# | Command Desk | https://acme-relay.local |
# | API | https://api.acme-relay.local |
# | Keycloak | https://auth.acme-relay.local |
# | GlitchTip | https://glitchtip.local |
# | Langfuse | https://langfuse.local |
# | Grafana | https://grafana.local |
#
# Plain `make demo` / `make up` still uses http://localhost:* without TLS.
#
# JWT `iss` must match the browser Keycloak URL (`KEYCLOAK_ISSUER=https://auth.acme-relay.local`).
# For live evals against TLS:
#
# ```bash
# SSL_CERT_FILE="$(mkcert -CAROOT)/rootCA.pem" \
#   API_URL=https://api.acme-relay.local \
#   KEYCLOAK_URL=https://auth.acme-relay.local \
#   make eval-host
# ```
#
# Certificates live in `infra/caddy/.certs/` (gitignored). Re-run `make tls-certs` to regenerate.
