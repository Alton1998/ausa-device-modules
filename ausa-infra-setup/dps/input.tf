variable "storage_account_name" {
  description = "Storage account name for IoT Hub"
  default = "ausa_iot_hub_storage_account"
}

variable "resource_group_name" {
  description = "Resource Group Name"
  default = "ausa_resource_group"
}
variable "resource_group_location" {
  default = "east_us"
  description = "Resource Group loac"
}

variable "storage_account_tier" {
  default = "Standard"
  description = "IoT Hub Storage Account Tier"
}

variable "account_replication_type" {
  default = "LRS"
  description = "IoT Hub Storage Account Replication Type"
}

variable "storage_container_name" {
  default = "ausa_iot_hub_storage_container"
  description = "IoT hub storage container name"
}

variable "storage_container_access_type" {
  default = "private"
  description = "IoT hub storage account access policy, default is private"
}

variable "ausa_event_hub_namespace" {
  default = "ausa"
  description = "Azure IoT hub event hub namespace"
}

variable "ausa_event_hub_namespace_tier" {
  default = "Basic"
  description = "Azure"
}

variable "ausa_event_hub_name" {
  default = "ausa_event_hub"
}

variable "ausa_event_hub_partition_count" {
  default = 2
}

variable "ausa_event_hub_message_retention" {
  default = 1
}

variable "ausa_event_hub_authorization_rule" {
  default = "ausa_event_hub_authorization_rule_iot_hub"
}

variable "ausa_dps_name" {
  default = "ausa_dps_name"
}