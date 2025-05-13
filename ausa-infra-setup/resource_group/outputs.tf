output "resource_group_name" {
  value = azurerm_resource_group.rg.name                                        # The actual value to be outputted
  description = "Azure Resource Group" # Description of what this output represents
}

output "resource_group_location" {
  value = azurerm_resource_group.rg.location
  description = "Azure Resource Group location"
}