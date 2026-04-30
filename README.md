# Self-Healing Microservices Cluster with Prometheus Monitoring

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)](https://www.ansible.com/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZD0iTTExLjk2IDExLjIzYy0xLjMyLS40MS0xLjc0LS44My0xLjc0LTEuNCAwLS42Ny42NS0xLjIyIDEuNjktMS4yMiAxLjA0IDAgMS44My42IDIuMDggMS40OGgxLjhjLS4yOC0xLjU1LTEuNjgtMi44OC0zLjgzLTIuODgtMi4yMiAwLTMuNiAxLjM0LTMuNiAyLjkyIDAgMS45MyAxLjU4IDIuNSAzLjMzIDMuMDMgMS40OC40NSAxLjc3Ljk1IDEuNzcgMS41OCAwIC44Ni0uODggMS40LTEuOTIgMS40LTEuMjkgMC0yLjI2LS43OC0yLjQzLTEuOEg3LjNjLjE4IDEuOTUgMS44NSAzLjE2IDQuMTQgMy4xNiAyLjQ1IDAgMy44Ni0xLjMgMy44Ni0zLjAzIDAtMS44OS0xLjM1LTIuNi0zLjM0LTMuMjR6bS04LjgxIDEuOWgyLjM4bC42OC0xLjkyaDIuOTVsLjY2IDEuOTJoMi40TDkuMDQgNi4wM0g2Ljg3bC0zLjcyIDcuMXptMy42Mi0zLjQ4bDEtMi45IDEuMDMgMi45SDYuNzd6TTI0IDYuMDNoLTIuMzFsLTEuOSA1LjU2LTEuNjgtNC45aC0uMThsLTEuNjYgNC45LTEuODktNS41NmgtMi4zbDMuMDUgNy4xaDIuMDhsMS40NS00LjQzIDEuNDcgNC40M2gyLjFMMjQgNi4wM3oiLz48L3N2Zz4K&logoColor=white)](https://aws.amazon.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

## Project Overview

This repository contains a robust infrastructure for deploying and managing a self-healing microservices cluster. The system leverages Prometheus for real-time monitoring and alerting, combined with automated recovery scripts to ensure high availability. The infrastructure is defined using Terraform, configured with Ansible, and runs containerized workloads.

## Key Features

- **Automated Infrastructure**: Provisioning of AWS resources using Terraform.
- **Microservices Architecture**: Containerized Node.js applications with built-in Prometheus metric exportation.
- **Monitoring and Alerting**: Comprehensive monitoring using Prometheus, Redis, and Alertmanager.
- **Self-Healing Capabilities**: Python-based monitoring scripts that automatically detect service failures and trigger recovery actions (e.g., EC2 reboots, service restarts).
- **Configuration Management**: Ansible roles for consistent server setup and security hardening.

## Repository Structure

- `node-metrics-app/`: A Node.js application demonstrating custom Prometheus metrics.
- `main.tf`: Terraform configuration for AWS infrastructure.
- `monitor.py`: Core self-healing logic for service health monitoring and automated recovery.
- `alertmanager-config.yaml`: Configuration for Prometheus Alertmanager.
- `playbook.yml`: Ansible playbook for environment orchestration.
- `roles/ssh/`: Ansible role for secure SSH configuration.
- `custom-alerts.yaml`: Definition of monitoring alert rules.

## Core Technologies

### Infrastructure as Code
The project uses Terraform to maintain a consistent state of the AWS environment, including EC2 instances and network configurations.

### Application Layer
The primary microservice is built with Node.js and Express, utilizing `prom-client` to expose metrics on a `/metrics` endpoint for scraping by Prometheus.

### Monitoring Stack
- **Prometheus**: Scrapes metrics from the microservices.
- **Redis**: Provides caching and data persistence for monitoring components.
- **Alertmanager**: Handles alerts sent by Prometheus and routes them to notification channels.

### Self-Healing Logic
Python scripts utilize `boto3` and `requests` to perform active health checks. If a service becomes unreachable or returns error codes, the script triggers an automated recovery process, including email notifications and instance reboots.

## Setup Instructions

### Prerequisites
- AWS Account and CLI configured.
- Terraform installed.
- Ansible installed.
- Node.js and Docker installed for local development.

### Deployment
1. **Initialize Infrastructure**:
   ```bash
   terraform init
   terraform apply
   ```
2. **Configure Servers**:
   ```bash
   ansible-playbook -i inventory.ini playbook.yml
   ```
3. **Deploy Microservices**:
   Navigate to `node-metrics-app/` and use the provided Dockerfile for containerization.

## Monitoring and Maintenance
The system is designed to be autonomous. Alerts are defined in `custom-alerts.yaml` and handled by `alertmanager-config.yaml`. The `monitor.py` script should be run as a scheduled task or service to ensure continuous self-healing coverage.
