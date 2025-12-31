variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout in seconds (should be 6x Lambda timeout)"
  type        = number
  default     = 720 # 6 * 120 seconds (2 min Lambda timeout)
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 86400 # 1 day
}

variable "max_receive_count" {
  description = "Number of times a message can be received before going to DLQ"
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
