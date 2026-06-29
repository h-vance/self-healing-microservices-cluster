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

## Run Ansible SSH Hardening

The sample inventory has no active hosts by default. Add target hosts before running:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
```

Expected result:

- Root SSH login is disabled on targeted hosts.
- SSH restarts only when configuration changes.
