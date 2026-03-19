resource "mongodbatlas_project" "project" {
  count  = var.atlas_create ? 1 : 0
  org_id = var.atlas_org_id
  name   = var.atlas_project_name
}

resource "mongodbatlas_database_user" "admin" {
  count              = var.atlas_create ? 1 : 0
  project_id         = mongodbatlas_project.project[0].id
  username           = "adminuser"
  password           = var.atlas_password
  auth_database_name = "admin"

  roles {
    role_name     = "atlasAdmin"
    database_name = "admin"
  }
}

resource "mongodbatlas_cluster" "cluster" {
  count                        = var.atlas_create ? 1 : 0
  project_id                   = mongodbatlas_project.project[0].id
  name                         = var.atlas_cluster_name
  cluster_type                 = "REPLICASET"
  provider_name                = "AWS"
  provider_region_name         = var.atlas_cluster_region_name
  provider_instance_size_name  = var.atlas_cluster_instance_size_name
  disk_size_gb                 = 10
  auto_scaling_disk_gb_enabled = true

  replication_specs {
    zone_name  = "Zone 1"
    num_shards = 1
    regions_config {
      region_name     = var.atlas_cluster_region_name
      electable_nodes = 3
      priority        = 7
      read_only_nodes = 0
      analytics_nodes = 0
    }
  }
}

# IP access list is no longer needed when using PrivateLink.
# Kept for local development or non-PrivateLink deployments.
resource "mongodbatlas_project_ip_access_list" "access" {
  for_each   = var.atlas_create && !var.aws_create ? toset(var.atlas_allowed_ips) : []
  project_id = mongodbatlas_project.project[0].id

  ip_address = strcontains(each.value, "/") ? null : each.value
  cidr_block = strcontains(each.value, "/") ? each.value : null

  comment = "Allowed IP ${each.value}"
}

output "connection_string" {
  value = var.atlas_create ? mongodbatlas_cluster.cluster[0].connection_strings[0].standard_srv : ""
}