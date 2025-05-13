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
  sku                 = var.ausa_event_hub_namespace_tier
}

resource "azurerm_eventhub" "ausa_eventhub" {
  name                = var.ausa_event_hub_name
  resource_group_name = var.resource_group_name
  namespace_name      = azurerm_eventhub_namespace.namespace.name
  partition_count     = var.ausa_event_hub_partition_count
  message_retention   = var.ausa_event_hub_message_retention
}

resource "azurerm_eventhub_authorization_rule" "my_terraform_authorization_rule" {
  resource_group_name = var.resource_group_name
  namespace_name      = azurerm_eventhub_namespace.namespace.name
  eventhub_name       = azurerm_eventhub.ausa_eventhub.name
  name                = "acctest"
  send                = true
}

resource "azurerm_iothub" "iothub" {
  name                = var.ausa_event_hub_authorization_rule
  resource_group_name = var.resource_group_name
  location            = var.resource_group_location

  sku {
    name     = "S1"
    capacity = 1
  }

  endpoint {
    type                       = "AzureIotHub.StorageContainer"
    connection_string          = azurerm_storage_account.sa.primary_blob_connection_string
    name                       = "export"
    batch_frequency_in_seconds = 60
    max_chunk_size_in_bytes    = 10485760
    container_name             = azurerm_storage_container.ausa_iot_hub_storage_container.name
    encoding                   = "Avro"
    file_name_format           = "{iothub}/{partition}_{YYYY}_{MM}_{DD}_{HH}_{mm}"
  }

  endpoint {
    type              = "AzureIotHub.EventHub"
    connection_string = azurerm_eventhub_authorization_rule.my_terraform_authorization_rule.primary_connection_string
    name              = "export2"
  }

  route {
    name           = "export"
    source         = "DeviceMessages"
    condition      = "true"
    endpoint_names = ["export"]
    enabled        = true
  }

  route {
    name           = "export2"
    source         = "DeviceMessages"
    condition      = "true"
    endpoint_names = ["export2"]
    enabled        = true
  }

  enrichment {
    key            = "tenant"
    value          = "$twin.tags.Tenant"
    endpoint_names = ["export", "export2"]
  }

  cloud_to_device {
    max_delivery_count = 30
    default_ttl        = "PT1H"
    feedback {
      time_to_live       = "PT1H10M"
      max_delivery_count = 15
      lock_duration      = "PT30S"
    }
  }

  tags = {
    purpose = "testing"
  }
}

resource "azurerm_iothub_shared_access_policy" "hub_access_policy" {
  name                = "terraform-policy"
  resource_group_name = var.resource_group_name
  iothub_name         = azurerm_iothub.iothub.name

  registry_read   = true
  registry_write  = true
  service_connect = true
}

resource "azurerm_iothub_dps" "dps" {
  name                = var.ausa_dps_name
  resource_group_name = var.resource_group_name
  location            = var.resource_group_location
  allocation_policy   = "Hashed"

  sku {
    name     = "S1"
    capacity = 1
  }

  linked_hub {
    connection_string       = azurerm_iothub_shared_access_policy.hub_access_policy.primary_connection_string
    location                = var.resource_group_location
    allocation_weight       = 150
    apply_allocation_policy = true
  }
}

resource "azurerm_iothub_certificate" "ausa_iot_hub_certificate" {
  name                = "ausa_iothub_certificate"
  resource_group_name = a
  iothub_name         = azurerm_iothub.iothub.name
  is_verified         = true

  certificate_content = filebase64("example.cer")
}

resource "azurerm_iothub_dps_certificate" "example" {
  name                = "ausa_dps_certificate"
  resource_group_name = var.resource_group_name
  iot_dps_name        = azurerm_iothub_dps.dps.name

  certificate_content = filebase64("example.cer")
}