resource "azurerm_storage_account" "sa" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.resource_group_location
  account_tier             = var.storage_account_tier
  account_replication_type = var.account_replication_type
}

resource "azurerm_storage_container" "ausa_iot_hub_storage_container" {
  name                  = var.storage_container_name
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = var.storage_container_access_type
}

resource "azurerm_eventhub_namespace" "namespace" {
  name                = var.ausa_event_hub_namespace
  resource_group_name = var.resource_group_name
  location            = var.resource_group_location
  sku                 = "Basic"
}