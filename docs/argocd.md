# Argo CD + Kubernetes (Relay)

Compose is the brief compliance path (`docker compose up`). Argo CD shows the **production GitOps** story: desired state in Git → cluster sync → self-heal.

## What we ship

| Path | Purpose |
|------|---------|
| [`infra/kubernetes/base/`](../infra/kubernetes/base/) | Namespace, API/worker/web Deployments+Services, secret example, Kustomize |
| [`infra/kubernetes/platform/argo-cd/applications.yaml`](../infra/kubernetes/platform/argo-cd/applications.yaml) | Argo CD `Application` CR pointing at `infra/kubernetes/base` |

## Bootstrap (kind / local)

```bash
# 1) Cluster + Argo CD (example)
kind create cluster --name relay
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2) Point Application at your repo (edit repoURL first)
kubectl apply -f infra/kubernetes/platform/argo-cd/applications.yaml

# 3) Secrets
kubectl -n relay-ops create secret generic relay-app-secrets --from-env-file=.env

# 4) Sync
argocd login localhost:8080   # or port-forward argocd-server
argocd app sync relay-ops-local
argocd app get relay-ops-local
```

## Panel talking points

1. **Git is source of truth** — change replicas in `api-deployment.yaml`, commit, Argo syncs.
2. **Automated sync + selfHeal** — drift is corrected (see `syncPolicy` on the Application).
3. **Scale-out seams** — `replicas: 2` on API/worker/web; Celery workers scale independently of chat API.
4. **Compose vs K8s** — laptop demo uses Compose; Argo CD is how Acme would promote staging→prod.

## Edit before real use

- Replace `repoURL: https://github.com/example/acme-relay.git` with your GitHub remote.
- Never commit real `secret.yaml`; use Sealed Secrets / External Secrets in production.
