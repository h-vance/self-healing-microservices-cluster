terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for the demo EC2 instance."
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "AMI ID for the demo EC2 instance. Default is Amazon Linux 2023 in us-east-1."
  type        = string
  default     = "ami-0c7217cdde317cfec"
}

variable "instance_type" {
  description = "EC2 instance size for the demo server."
  type        = string
  default     = "t3.micro"
}

variable "project_tags" {
  description = "Tags applied to provisioned demo resources."
  type        = map(string)
  default = {
    Project     = "self-healing-microservices-cluster"
    Environment = "demo"
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "web_server" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = merge(
    var.project_tags,
    {
      Name = "self-healing-demo-server"
    }
  )
}

output "web_server_id" {
  description = "ID of the demo EC2 instance."
  value       = aws_instance.web_server.id
}

output "web_server_public_ip" {
  description = "Public IP of the demo EC2 instance."
  value       = aws_instance.web_server.public_ip
}
