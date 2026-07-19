# Runbook: prompt rollback

## Symptoms

- Sudden drop in eval scores or groundedness pass rate
- Governance UI shows unexpected production prompt version

## Steps

1. Identify last known-good version in `apps/api/prompts/relay-system.yaml` / `prompt_versions`
2. Revert YAML, redeploy API
3. Confirm `prompt_name` / `prompt_version` on a new chat response
4. Re-run `make eval-host` and compare `evals/eval_results.md`
