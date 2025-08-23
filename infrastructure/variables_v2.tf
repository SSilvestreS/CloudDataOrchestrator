# =============================================================================
# CloudDataOrchestrator v2.0 - Variáveis Terraform
# =============================================================================

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente (staging, production)"
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment deve ser 'staging' ou 'production'."
  }
}

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "clouddataorchestrator"
}

# =============================================================================
# NETWORKING
# =============================================================================

variable "vpc_cidr" {
  description = "CIDR block para VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnets" {
  description = "CIDR blocks para subnets privadas"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks para subnets públicas"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# =============================================================================
# CONTAINER SETTINGS
# =============================================================================

variable "image_repository" {
  description = "Repositório da imagem Docker"
  type        = string
  default     = "ghcr.io/ssilvestres/clouddataorchestrator"
}

variable "image_tag" {
  description = "Tag da imagem Docker"
  type        = string
  default     = "latest"
}

# =============================================================================
# ECS SETTINGS
# =============================================================================

variable "api_cpu" {
  description = "CPU para container da API"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memória para container da API"
  type        = number
  default     = 1024
}

variable "api_instance_count" {
  description = "Número de instâncias da API"
  type        = number
  default     = 2
}

variable "dashboard_cpu" {
  description = "CPU para container do dashboard"
  type        = number
  default     = 256
}

variable "dashboard_memory" {
  description = "Memória para container do dashboard"
  type        = number
  default     = 512
}

variable "dashboard_instance_count" {
  description = "Número de instâncias do dashboard"
  type        = number
  default     = 1
}

# =============================================================================
# SECURITY
# =============================================================================

variable "api_token" {
  description = "Token de API para autenticação"
  type        = string
  sensitive   = true
}

# =============================================================================
# MONITORING
# =============================================================================

variable "log_retention_days" {
  description = "Dias de retenção dos logs"
  type        = number
  default     = 30
}
