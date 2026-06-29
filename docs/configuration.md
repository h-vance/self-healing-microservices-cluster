# Configuration

This page lists the repo configuration surfaces and their safe defaults.

## Environment Variables

Use `.env.example` as a local template. Do not commit real secrets.

| Variable | Used by | Default | Purpose |
| --- | --- | --- | --- |
| `PORT` | `node-metrics-app/index.js` | `3000` | HTTP port for the metrics app |

## Terraform Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `aws_region` | `us-east-1` | AWS region for the demo EC2 instance |
| `ami_id` | `ami-0c7217cdde317cfec` | AMI ID for the demo EC2 instance |
| `instance_type` | `t3.micro` | EC2 instance type |
| `project_tags` | project, environment, managed-by tags | Tags applied to demo resources |

Example:

```bash
cd terraform
terraform plan \
  -var='aws_region=us-east-1' \
  -var='ami_id=ami-0c7217cdde317cfec' \
  -var='instance_type=t3.micro'
```

## Helm Values

| Value | Default | Purpose |
| --- | --- | --- |
| `mongodb.replicaCount` | `1` | MongoDB demo replica count |
| `mongodb.image` | `mongo:7.0` | MongoDB image tag |
| `mongodb.port` | `27017` | MongoDB container and service port |
| `mongodb.resources` | CPU and memory requests/limits | MongoDB resource controls |
| `mongoExpress.replicaCount` | `1` | mongo-express demo replica count |
| `mongoExpress.image` | `mongo-express:1.0.2` | mongo-express image tag |
| `mongoExpress.port` | `8081` | mongo-express HTTP port |
| `mongoExpress.service.type` | `ClusterIP` | Service exposure type |
| `mongoExpress.resources` | CPU and memory requests/limits | mongo-express resource controls |
| `secrets.mongoRootUsername` | `root` | Demo MongoDB username |
| `secrets.mongoRootPassword` | placeholder | Demo MongoDB password |

Render with overrides:

```bash
helm template mongo-stack mongo-stack \
  --set mongoExpress.service.type=ClusterIP
```

## Kubernetes Placeholders

Standalone Secret manifests under `k8s/` contain placeholder values. Replace them through your cluster's secret delivery process before using the manifests outside a demo environment.
