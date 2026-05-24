# Self-Healing Microservices Cluster with Prometheus Monitoring

> **Automated infrastructure recovery and observability for containerized microservices on AWS.**

[![Python](https://www.shieldcn.dev/badge/Python-3776AB.svg?variant=default&logo=Python&logoColor=FFFFFF&size=xs)](https://www.python.org/)
[![Node.js](https://www.shieldcn.dev/badge/Node.js-339933.svg?variant=default&logo=Node.js&logoColor=FFFFFF&size=xs)](https://nodejs.org/)
[![Prometheus](https://www.shieldcn.dev/badge/Prometheus-E6522C.svg?variant=default&logo=Prometheus&logoColor=FFFFFF&size=xs)](https://prometheus.io/)
[![Redis](https://www.shieldcn.dev/badge/Redis-DC382D.svg?variant=default&logo=Redis&logoColor=FFFFFF&size=xs)](https://redis.io/)
[![Terraform](https://www.shieldcn.dev/badge/Terraform-7B42BC.svg?variant=default&logo=Terraform&logoColor=FFFFFF&size=xs)](https://www.terraform.io/)
[![Ansible](https://www.shieldcn.dev/badge/Ansible-EE0000.svg?variant=default&logo=Ansible&logoColor=FFFFFF&size=xs)](https://www.ansible.com/)
[![AWS](https://www.shieldcn.dev/badge/AWS-232F3E.svg?variant=default&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZD0iTTExLjk2IDExLjIzYy0xLjMyLS40MS0xLjc0LS44My0xLjc0LTEuNCAwLS42Ny42NS0xLjIyIDEuNjktMS4yMiAxLjA0IDAgMS44My42IDIuMDggMS40OGgxLjhjLS4yOC0xLjU1LTEuNjgtMi44OC0zLjgzLTIuODgtMi4yMiAwLTMuNiAxLjM0LTMuNiAyLjkyIDAgMS45MyAxLjU4IDIuNSAzLjMzIDMuMDMgMS40OC40NSAxLjc3Ljk1IDEuNzcgMS41OCAwIC44Ni0uODggMS40LTEuOTIgMS40LTEuMjkgMC0yLjI2LS43OC0yLjQzLTEuOEg3LjNjLjE4IDEuOTUgMS44NSAzLjE2IDQuMTQgMy4xNiAyLjQ1IDAgMy44Ni0xLjMgMy44Ni0zLjAzIDAtMS44OS0xLjM1LTIuNi0zLjM0LTMuMjR6bS04LjgxIDEuOWgyLjM4bC42OC0xLjkyaDIuOTVsLjY2IDEuOTJoMi40TDkuMDQgNi4wM0g2Ljg3bC0zLjcyIDcuMXptMy42Mi0zLjQ4bDEtMi45IDEuMDMgMi45SDYuNzd6TTI0IDYuMDNoLTIuMzFsLTEuOSA1LjU2LTEuNjgtNC45aC0uMThsLTEuNjYgNC45LTEuODktNS41NmgtMi4zbDMuMDUgNy4xaDIuMDhsMS40NS00LjQzIDEuNDcgNC40M2gyLjFMMjQgNi4wM3oiLz48L3N2Zz4K&logoColor=FFFFFF&size=xs)](https://aws.amazon.com/)
[![Docker](https://www.shieldcn.dev/badge/Docker-2496ED.svg?variant=default&logo=Docker&logoColor=FFFFFF&size=xs)](https://www.docker.com/)

---

## The Problem

**The Symptom:** Microservices went down during off-hours and nobody noticed until customers reported it. Recovery required manual SSH access, log inspection, and instance reboots — each incident taking 30+ minutes of reactive firefighting.

**The Investigation:** The stack had monitoring but no automated response. Prometheus collected metrics and Alertmanager fired alerts, but there was no mechanism to act on those alerts without human intervention. Backup and restore procedures were documented but rarely tested.

**The Resolution:** A self-healing cluster that combines Prometheus-based observability with Python-driven recovery automation. When a service fails health checks, the system automatically reboots the affected instance, sends email notification, and logs the event. Backup, restore, and cleanup scripts run on a schedule to ensure data durability.

---

## Architecture

```text
                         ┌─────────────────────┐
                         │   Prometheus         │
                         │   (Metrics & Alerts) │
                         └──────┬──────┬────────┘
                                │      │
                    ┌───────────┘      └───────────┐
                    ▼                              ▼
         ┌──────────────────┐          ┌───────────────────┐
         │   Node Metrics   │          │  Alertmanager      │
         │   (Express App)  │          │  (Alert Routing)   │
         └──────────────────┘          └───────────────────┘
                                                    │
                                                    ▼
         ┌──────────────────┐          ┌───────────────────┐
         │   monitor.py     │─────────▶│  EC2 Reboot +     │
         │   (Health Check) │          │  Email Notify     │
         └──────────────────┘          └───────────────────┘
                                                    │
         ┌──────────────────┐                       │
         │   backup.py      │───────────────────────┤
         │   restore.py     │───────────────────────┤
         │   cleanup.py     │───────────────────────┘
         └──────────────────┘
```

---

## Script Reference

| Script | Purpose | Trigger |
| ------- | --------- | --------- |
| `scripts/monitor.py` | Health-check a target URL, reboot EC2 on failure, send email | Manual / cron |
| `scripts/health_check.py` | Scheduled EC2 instance state polling every 10 seconds | Continuous |
| `scripts/backup.py` | Create EBS snapshots for all attached volumes | Cron |
| `scripts/restore.py` | Restore a volume from a specific snapshot and attach to instance | Manual |
| `scripts/cleanup.py` | Delete old snapshots tagged as "Automated Backup" | Cron |
| `scripts/zero_leak.py` | Find snapshots older than 30 days (dry-run by default) | Manual review |
| `scripts/add_tags.py` | Tag all EC2 instances with `Environment: Dev` | One-time setup |

### monitor.py — Self-Healing Core

The primary recovery script. Performs an HTTP GET against the target URL and:

- If **200 OK** — logs success, takes no action.
- If **non-200** — sends an email alert via SMTP and reboots the EC2 instance.
- If **unreachable** (timeout / connection error) — sends an alert and reboots the instance.

```bash
python scripts/monitor.py
```

### backup.py — EBS Snapshot Automation

Creates snapshots of every EBS volume in the `us-east-1` region with description "Automated Backup". Intended to run daily via cron.

```bash
python scripts/backup.py
```

### restore.py — Volume Recovery

Restores a volume from a specific snapshot ID and attaches it to a target instance as `/dev/sdf`. Update `snapshot_id` and `instance_id` inside the script before running.

```bash
python scripts/restore.py
```

### cleanup.py — Snapshot Lifecycle

Deletes all snapshots with the "Automated Backup" description — designed to run after a successful restore to prevent accumulation.

```bash
python scripts/cleanup.py
```

### zero_leak.py — Stale Snapshot Audit

Identifies snapshots older than 30 days (cross-account, dry-run). Uncomment the delete line to enable automatic removal.

```bash
python scripts/zero_leak.py
```

### health_check.py — Continuous State Monitoring

Polls EC2 `DescribeInstances` every 10 seconds and prints instance state. Useful for monitoring recovery progress after a reboot.

```bash
python scripts/health_check.py
```

### add_tags.py — Resource Labeling

Tags all EC2 instances in `us-east-1` with `Environment: Dev`. Run once during initial provisioning.

```bash
python scripts/add_tags.py
```

---

## Monitoring Stack

### Prometheus & Alertmanager

| Component | Configuration | Purpose |
| ----------- | --------------- | --------- |
| Prometheus | `prometheus.yml` | Scrapes `/metrics` from node-metrics-app |
| Alertmanager | `k8s/alertmanager-config.yaml` | Routes alerts to notification channels |
| Custom Rules | `k8s/custom-alerts.yaml` | Predefined alerts (HighCPUUsage, PodFailedToStart) |
| Redis Alerts | `k8s/redis-alerts.yaml` | Redis-specific monitoring rules |
| ServiceMonitor | `k8s/redis-servicemonitor.yaml` | Prometheus Operator scrape configuration |

The custom alert rules detect:
- **HighCPUUsage** — instance CPU above 50% for 5 minutes (warning)
- **PodFailedToStart** — pods in Failed/Unknown/Pending state for 5 minutes (critical)

### Node.js Metrics Application

The `node-metrics-app/` directory contains an Express.js application that uses `prom-client` to expose custom metrics on a `/metrics` endpoint for Prometheus scraping.

```bash
cd node-metrics-app
npm install
npm start
```

---

## Kubernetes Resources

The cluster includes Kubernetes manifests for stateful workloads:

| Manifest | Resource | Description |
| ---------- | ---------- | ------------- |
| `k8s/mongo-config.yaml` | ConfigMap | MongoDB configuration |
| `k8s/mongo-secret.yaml` | Secret | MongoDB authentication credentials |
| `k8s/mongo-service.yaml` | Service | MongoDB internal service exposure |
| `k8s/mongo-express.yaml` | Deployment | Web-based MongoDB admin interface |
| `k8s/mongo-express-service.yaml` | Service | mongo-express external access |
| `k8s/redis-alerts.yaml` | PrometheusRule | Redis-specific alert definitions |
| `k8s/redis-servicemonitor.yaml` | ServiceMonitor | Prometheus scrape target for Redis |
| `k8s/pod-viewer-role.yaml` | ClusterRole | Read-only pod access |
| `k8s/pod-viewer-binding.yaml` | RoleBinding | Bind viewer role to service account |
| `k8s/private-deployment.yaml` | Deployment | Sample private deployment |

---

## Infrastructure Provisioning

### Terraform (`terraform/main.tf`)

Defines the core AWS infrastructure: EC2 instances, networking, and security groups.

```bash
cd terraform
terraform init
terraform apply
```

### Ansible (`ansible/playbook.yml`)

Configures provisioned servers. Applies the `ssh` role for secure SSH configuration.

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

---

## Prerequisites

- **AWS Account** with CLI configured (`aws configure`)
- **Python 3.8+** with `boto3`, `requests`, `schedule` installed
- **Terraform** for infrastructure provisioning
- **Ansible** for configuration management
- **Node.js 18+** and Docker for local microservice development
- **kubectl** for Kubernetes manifest deployment

---

## Deployment

1. **Provision infrastructure**
   ```bash
   terraform init
   terraform apply
   ```

2. **Configure servers**
   ```bash
   ansible-playbook -i inventory.ini playbook.yml
   ```

3. **Deploy monitoring stack** (Prometheus + Alertmanager)
4. **Run self-healing script** as a scheduled task or systemd service
   ```bash
   # Add to crontab for continuous coverage:
   # * * * * * cd /path/to/repo && python monitor.py
   ```

5. **Schedule backups**
   ```bash
   # Daily EBS snapshots:
   # 0 2 * * * cd /path/to/repo && python backup.py
   ```

---

## Safety

- `monitor.py` contains hardcoded credentials (SMTP password) — rotate before production use.
- `restore.py` attaches volumes to a running instance — verify the device path is unused.
- `cleanup.py` permanently deletes snapshots — run `zero_leak.py` first to audit what will be removed.
- The `POST /admin/toggle-health` endpoint in `cloud-service-baseline` is for testing only — do not expose in production.

---

## Related Repositories

| Repository | Description |
| ---------- | ----------- |
| [**cloud-service-baseline**](https://github.com/h-vance/cloud-service-baseline) | Baseline health validation and configuration verification for cloud services |
| [**ops-diagnostics**](https://github.com/h-vance/ops-diagnostics) | Diagnostic scripts for automated health verification, log analysis, and system profiling |
| [**systems-debugging-framework**](https://github.com/h-vance/systems-debugging-framework) | Structured triage checklists for network, system, and application fault isolation |

---

Maintained by Harrison Vance — Technical Support & Operations
