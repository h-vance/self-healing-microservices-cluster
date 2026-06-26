# Runbooks

These runbooks are designed for local validation and safe demos. Commands that can mutate AWS resources are dry-run by default and require `--execute`.

## Validate The Metrics App

```bash
cd node-metrics-app
npm ci
npm test
node -c index.js
```

Expected result:

- Tests pass for `/healthz`, `/`, and `/metrics`.
- `node -c index.js` exits without output.

## Run The Metrics App Locally

```bash
cd node-metrics-app
PORT=3000 npm start
```

In another terminal:

```bash
curl http://127.0.0.1:3000/healthz
curl http://127.0.0.1:3000/
curl http://127.0.0.1:3000/metrics
```

Expected result:

- `/healthz` returns `{"status":"ok"}`.
- `/` increments `my_custom_metric_total`.
- `/metrics` exposes Prometheus text output.

## Validate Kubernetes Manifests

```bash
python3 - <<'PY'
import pathlib
import yaml

files = (
    list(pathlib.Path("k8s").glob("*.yaml"))
    + list(pathlib.Path("mongo-k8s").glob("*.yaml"))
    + list(pathlib.Path("node-metrics-app").glob("*.yaml"))
)

for path in files:
    list(yaml.safe_load_all(path.read_text()))
    print(f"ok {path}")
PY
```

Expected result:

- Each non-template YAML file parses successfully.

## Render The Helm Chart

```bash
helm lint mongo-stack
helm template mongo-stack mongo-stack
```

Expected result:

- Helm lint reports zero chart failures.
- Template rendering emits MongoDB, mongo-express, service, config, and secret resources.

## Validate Terraform

```bash
terraform fmt -check -recursive
cd terraform
terraform init -backend=false
terraform validate
```

Expected result:

- Terraform formatting passes.
- Provider init completes.
- Validation reports that the configuration is valid.

## Dry-Run URL Recovery

```bash
python3 scripts/monitor.py --url https://example.com --instance-id i-00000000000000000
```

Expected result:

- If the URL is healthy, the script exits cleanly.
- If unhealthy, the script prints the recovery action without rebooting anything.

To run live recovery, provide real configuration and add `--execute`:

```bash
python3 scripts/monitor.py \
  --url https://example.com \
  --instance-id i-00000000000000000 \
  --region us-east-1 \
  --execute
```

## Dry-Run EBS Backups

```bash
python3 scripts/backup.py --region us-east-1
```

Expected result:

- The script lists snapshots it would create.
- No snapshots are created without `--execute`.

Live mode:

```bash
python3 scripts/backup.py --region us-east-1 --execute
```

## Dry-Run Snapshot Cleanup

```bash
python3 scripts/cleanup.py --region us-east-1 --older-than-days 30
python3 scripts/zero_leak.py --region us-east-1 --older-than-days 30
```

Expected result:

- The scripts list snapshots they would delete.
- No snapshots are deleted without `--execute`.

## Restore From Snapshot

Always dry-run first:

```bash
python3 scripts/restore.py \
  --snapshot-id snap-00000000000000000 \
  --instance-id i-00000000000000000 \
  --availability-zone us-east-1a
```

Live mode:

```bash
python3 scripts/restore.py \
  --snapshot-id snap-00000000000000000 \
  --instance-id i-00000000000000000 \
  --availability-zone us-east-1a \
  --execute
```

## Run Ansible SSH Hardening

The sample inventory has no active hosts by default. Add target hosts before running:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
```

Expected result:

- Root SSH login is disabled on targeted hosts.
- SSH restarts only when configuration changes.
