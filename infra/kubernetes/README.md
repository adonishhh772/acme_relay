# Relay Kubernetes

Kustomize base under `base/` includes:

- Deployments/Services: `relay-api`, `relay-worker`, `relay-web`
- MCP Deployments/Services: domain / filesystem / postgres
- Ingress (`app.relay.local`, `api.relay.local`)
- NetworkPolicies (default-deny + allowlists for ingress, API, MCP, DB, Redis)
- Secret example (copy to a real secret; never commit credentials)

```bash
make kustomize-build
kubectl apply -k infra/kubernetes/base
kubectl apply -f infra/kubernetes/platform/argo-cd/applications.yaml
```

See [docs/argocd.md](../../docs/argocd.md) and [docs/production-readiness.md](../../docs/production-readiness.md).
