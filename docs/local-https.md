# Local HTTPS via Caddy + mkcert

`make demo` / `make up` start the stack **with TLS by default** (Caddy + mkcert hostnames).

## Prerequisites

```bash
brew install mkcert nss   # once
```

`make demo` runs `scripts/setup-local-tls.sh` automatically (installs local CA, writes certs under `infra/caddy/.certs/`, ensures `/etc/hosts`).

## URLs

| Service | URL |
|---------|-----|
| Command Desk | https://acme-relay.local |
| API | https://api.acme-relay.local |
| Keycloak | https://auth.acme-relay.local |
| GlitchTip | https://glitchtip.local |
| Langfuse | https://langfuse.local |
| Grafana | https://grafana.local |

## Commands

```bash
make demo        # certs + compose (TLS overlay)
make down        # tear down TLS stack
make demo-http   # escape hatch: http://localhost:* without Caddy
make tls-certs   # regenerate certs / hosts only
```

`make tls-up` is an alias for `make demo`.

## Auth / evals

JWT `iss` must be `https://auth.acme-relay.local` when the desk uses HTTPS.

```bash
make eval-host
# uses API_URL=https://api.acme-relay.local and SSL_CERT_FILE from mkcert CA
```

Certificates live in `infra/caddy/.certs/` (gitignored). Re-run `make tls-certs` to regenerate.
