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

variable "azurerm_storage_container_name" {
  default = "ausa_iot_hub_storage_container"
  description = "IoT hub storage container name"
}