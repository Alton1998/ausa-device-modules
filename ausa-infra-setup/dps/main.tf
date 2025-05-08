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
  container_access_type = "private"
}

resource "azurerm_eventhub_namespace" "namespace" {
  name                = random_pet.eventhub_namespace_name.id
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
}