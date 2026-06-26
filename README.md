# Self-Healing Microservices Cluster

Demo infrastructure for a monitored Kubernetes workload, Prometheus scraping, AWS recovery scripts, Terraform validation, and Ansible hardening examples.

This repository is portfolio-oriented. It shows the shape of a cloud/SRE project while keeping cloud-mutating automation dry-run by default.

## What Is Included

- `node-metrics-app/`: Express service with `/`, `/healthz`, and `/metrics` endpoints.
- `node-metrics-app/node-app.yaml`: Kubernetes deployment and service for the metrics app.
- `k8s/` and `mongo-k8s/`: standalone Kubernetes manifests for MongoDB, mongo-express, RBAC, alerts, and demo workloads.
- `mongo-stack/`: Helm chart for rendering the MongoDB and mongo-express stack.
- `terraform/`: small AWS EC2 example with pinned provider constraints and validation-friendly variables.
- `scripts/`: AWS recovery, backup, restore, tagging, and cleanup utilities.
- `ansible/`: SSH hardening role and small fleet utility examples.

## Safety Notes

- The checked-in Kubernetes Secret values are fake demo placeholders. Replace them before applying manifests to a real cluster.
- AWS scripts default to read-only or dry-run behavior. Pass `--execute` only when you intend to mutate cloud resources.
- The MongoDB examples are demo deployments. They do not include persistent volumes, network policies, external secret management, or high availability.
- Rotate any credentials that were ever committed before this hardening pass. In particular, treat previous SMTP app passwords as compromised.

## Local Validation

Run the checks from the repository root:

```bash
cd node-metrics-app
npm ci
npm test
node -c index.js
cd ..

helm lint mongo-stack
helm template mongo-stack mongo-stack

terraform fmt -check -recursive
cd terraform
terraform init -backend=false
terraform validate
```

The GitHub Actions workflow runs the same core checks on push and pull request to `main`.

## Run The Metrics App

```bash
cd node-metrics-app
npm ci
PORT=3000 npm start
```

Endpoints:

- `GET /healthz`: returns a simple health response.
- `GET /`: increments `my_custom_metric_total`.
- `GET /metrics`: exposes Prometheus metrics.

Build the container locally:

```bash
cd node-metrics-app
docker build -t node-metrics-app:local .
```

## Kubernetes And Helm

Standalone metrics app deployment:

```bash
kubectl apply -f node-metrics-app/node-app.yaml
kubectl apply -f node-metrics-app/service-monitor.yaml
```

Helm render and install:

```bash
helm template mongo-stack mongo-stack
helm install mongo-stack mongo-stack
```

The manifests use pinned example image tags, probes, resource requests and limits, and basic security contexts. For production, add persistent storage, network policies, external secret delivery, backup verification, and multi-replica service design.

## AWS Utility Scripts

Examples:

```bash
python3 scripts/monitor.py --url https://example.com
python3 scripts/backup.py --region us-east-1
python3 scripts/cleanup.py --older-than-days 30
python3 scripts/restore.py --snapshot-id snap-123 --instance-id i-123 --availability-zone us-east-1a
python3 scripts/add_tags.py --key Environment --value Dev
```

Add `--execute` to scripts that support mutation after reviewing the dry-run output.

`scripts/monitor.py` reads optional notification and recovery settings from environment variables:

- `MONITOR_URL`
- `RECOVERY_INSTANCE_ID`
- `AWS_REGION`
- `SMTP_SENDER`
- `SMTP_RECEIVER`
- `SMTP_PASSWORD`

## Terraform

The Terraform example provisions one demo EC2 instance.

```bash
cd terraform
terraform init -backend=false
terraform validate
terraform plan
```

Set a different AMI, region, or instance type with variables:

```bash
terraform plan \
  -var='aws_region=us-east-1' \
  -var='ami_id=ami-0c7217cdde317cfec' \
  -var='instance_type=t3.micro'
```

## Ansible

The SSH role disables root SSH login and restarts SSH when the config changes.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
```

The sample inventory has no active hosts by default.

## Known Limitations

- No end-to-end live cluster test is included.
- No production secret manager is wired in.
- MongoDB has no persistence in the demo manifests.
- Terraform is intentionally minimal and does not create a full VPC, EKS cluster, IAM boundary, or observability stack.
- Docker image tags such as `w0nky/my-node-metrics:1.0.0` assume the image has been built and published under that tag.
