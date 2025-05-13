
module "resource_group" {
  source                  = "./resource_group"
  resource_group_location = var.resource_group_name
  resource_group_name     = var.resource_group_location
}

module "dps" {
  source                  = "./dps"
  resource_group_location = module.resource_group.resource_group_location
  resource_group_name     = module.resource_group.resource_group_name
}