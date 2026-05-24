# Self-Healing Microservices Cluster with Prometheus Monitoring

> **Automated infrastructure recovery and observability for containerized microservices on AWS.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=FFFFFF)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=Node.js&logoColor=FFFFFF)](https://nodejs.org/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=FFFFFF)](https://prometheus.io/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=Redis&logoColor=FFFFFF)](https://redis.io/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=Terraform&logoColor=FFFFFF)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=Ansible&logoColor=FFFFFF)](https://www.ansible.com/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZD0iTTExLjk2IDExLjIzYy0xLjMyLS40MS0xLjc0LS44My0xLjc0LTEuNCAwLS42Ny42NS0xLjIyIDEuNjktMS4yMiAxLjA0IDAgMS44My42IDIuMDggMS40OGgxLjhjLS4yOC0xLjU1LTEuNjgtMi44OC0zLjgzLTIuODgtMi4yMiAwLTMuNiAxLjM0LTMuNiAyLjkyIDAgMS45MyAxLjU4IDIuNSAzLjMzIDMuMDMgMS40OC40NSAxLjc3Ljk1IDEuNzcgMS41OCAwIC44Ni0uODggMS40LTEuOTIgMS40LTEuMjkgMC0yLjI2LS43OC0yLjQzLTEuOEg3LjNjLjE4IDEuOTUgMS44NSAzLjE2IDQuMTQgMy4xNiAyLjQ1IDAgMy44Ni0xLjMgMy44Ni0zLjAzIDAtMS44OS0xLjM1LTIuNi0zLjM0LTMuMjR6bS04LjgxIDEuOWgyLjM4bC42OC0xLjkyaDIuOTVsLjY2IDEuOTJoMi40TDkuMDQgNi4wM0g2Ljg3bC0zLjcyIDcuMXptMy42Mi0zLjQ4bDEtMi45IDEuMDMgMi45SDYuNzd6TTI0IDYuMDNoLTIuMzFsLTEuOSA1LjU2LTEuNjgtNC45aC0uMThsLTEuNjYgNC45LTEuODktNS41NmgtMi4zbDMuMDUgNy4xaDIuMDhsMS40NS00LjQzIDEuNDcgNC40M2gyLjFMMjQgNi4wM3oiLz48L3N2Zz4K&logoColor=FFFFFF)](https://aws.amazon.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=FFFFFF)](https://www.docker.com/)

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
| `monitor.py` | Health-check a target URL, reboot EC2 on failure, send email | Manual / cron |
| `health_check.py` | Scheduled EC2 instance state polling every 10 seconds | Continuous |
| `backup.py` | Create EBS snapshots for all attached volumes | Cron |
| `restore.py` | Restore a volume from a specific snapshot and attach to instance | Manual |
| `cleanup.py` | Delete old snapshots tagged as "Automated Backup" | Cron |
| `zero_leak.py` | Find snapshots older than 30 days (dry-run by default) | Manual review |
| `add_tags.py` | Tag all EC2 instances with `Environment: Dev` | One-time setup |

### monitor.py — Self-Healing Core

The primary recovery script. Performs an HTTP GET against the target URL and:

- If **200 OK** — logs success, takes no action.
- If **non-200** — sends an email alert via SMTP and reboots the EC2 instance.
- If **unreachable** (timeout / connection error) — sends an alert and reboots the instance.

```bash
python monitor.py
```

### backup.py — EBS Snapshot Automation

Creates snapshots of every EBS volume in the `us-east-1` region with description "Automated Backup". Intended to run daily via cron.

```bash
python backup.py
```

### restore.py — Volume Recovery

Restores a volume from a specific snapshot ID and attaches it to a target instance as `/dev/sdf`. Update `snapshot_id` and `instance_id` inside the script before running.

```bash
python restore.py
```

### cleanup.py — Snapshot Lifecycle

Deletes all snapshots with the "Automated Backup" description — designed to run after a successful restore to prevent accumulation.

```bash
python cleanup.py
```

### zero_leak.py — Stale Snapshot Audit

Identifies snapshots older than 30 days (cross-account, dry-run). Uncomment the delete line to enable automatic removal.

```bash
python zero_leak.py
```

### health_check.py — Continuous State Monitoring

Polls EC2 `DescribeInstances` every 10 seconds and prints instance state. Useful for monitoring recovery progress after a reboot.

```bash
python health_check.py
```

### add_tags.py — Resource Labeling

Tags all EC2 instances in `us-east-1` with `Environment: Dev`. Run once during initial provisioning.

```bash
python add_tags.py
```

---

## Monitoring Stack

### Prometheus & Alertmanager

| Component | Configuration | Purpose |
| ----------- | --------------- | --------- |
| Prometheus | `prometheus.yml` | Scrapes `/metrics` from node-metrics-app |
| Alertmanager | `alertmanager-config.yaml` | Routes alerts to notification channels |
| Custom Rules | `custom-alerts.yaml` | Predefined alerts (HighCPUUsage, PodFailedToStart) |
| Redis Alerts | `redis-alerts.yaml` | Redis-specific monitoring rules |
| ServiceMonitor | `redis-servicemonitor.yaml` | Prometheus Operator scrape configuration |

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
| `mongo-config.yaml` | ConfigMap | MongoDB configuration |
| `mongo-secret.yaml` | Secret | MongoDB authentication credentials |
| `mongo-service.yaml` | Service | MongoDB internal service exposure |
| `mongo-express.yaml` | Deployment | Web-based MongoDB admin interface |
| `mongo-express-service.yaml` | Service | mongo-express external access |
| `redis-alerts.yaml` | PrometheusRule | Redis-specific alert definitions |
| `redis-servicemonitor.yaml` | ServiceMonitor | Prometheus scrape target for Redis |
| `pod-viewer-role.yaml` | ClusterRole | Read-only pod access |
| `pod-viewer-binding.yaml` | RoleBinding | Bind viewer role to service account |
| `private-deployment.yaml` | Deployment | Sample private deployment |

---

## Infrastructure Provisioning

### Terraform (`main.tf`)

Defines the core AWS infrastructure: EC2 instances, networking, and security groups.

```bash
terraform init
terraform apply
```

### Ansible (`playbook.yml`)

Configures provisioned servers. Applies the `ssh` role for secure SSH configuration.

```bash
ansible-playbook -i inventory.ini playbook.yml
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
