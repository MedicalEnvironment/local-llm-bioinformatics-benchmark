variable "subscription_id" {
  description = "Azure subscription ID (az account show --query id -o tsv)."
  type        = string
}

variable "resource_group_name" {
  description = "New resource group that will hold every resource of the run."
  type        = string
  default     = "rg-llm-bench-neu"
}

variable "location" {
  description = "Region with T4 (NCasT4_v3) quota. In the original run only northeurope had any."
  type        = string
  default     = "northeurope"
}

variable "vm_size" {
  description = "Standard_NC4as_T4_v3 (28 GB RAM) was the only size with capacity on 2026-10-29. NC8as/NC16as give more RAM for MoE offload."
  type        = string
  default     = "Standard_NC4as_T4_v3"
}

variable "zone" {
  description = "Availability zone (\"1\", \"2\", \"3\") or null to let Azure choose. Try each zone if allocation fails."
  type        = string
  default     = null
}

variable "admin_username" {
  type    = string
  default = "llmbench"
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}

variable "allowed_ssh_cidrs" {
  description = "Operator IPs allowed to SSH in, e.g. [\"203.0.113.7/32\"]. Never 0.0.0.0/0."
  type        = list(string)
}

variable "os_disk_size_gb" {
  description = "Room for the models (about 45 GB for the four T4 models) plus llama.cpp and results."
  type        = number
  default     = 256
}

variable "auto_shutdown_utc" {
  description = "Daily deallocation time, HHMM in UTC."
  type        = string
  default     = "2300"
}

variable "tags" {
  type    = map(string)
  default = { purpose = "llm-benchmark" }
}
