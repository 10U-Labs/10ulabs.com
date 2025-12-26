variable "cluster_name" {
  type = string
}

variable "container_name" {
  type = string
}

variable "task_family" {
  type = string
}

variable "log_stream_prefix" {
  type = string
}

variable "fargate_cpu" {
  type = string
}

variable "fargate_memory" {
  type = string
}

variable "fargate_cpu_architecture" {
  type = string
}

variable "fargate_operating_system_family" {
  type = string
}
