terraform {
  required_version = ">= 0.13.1"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }

    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "1.40.0"
    }
  }

  backend "local" {
    path = "/states/terraform.tfstate"
  }
}

provider "aws" {
  default_tags {
    tags = {
      purpose      = "partners"
      owner        = "mohammaddaoud.farooqi@mongodb.com"
      OwnerContact = "mohammaddaoud.farooqi@mongodb.com"
      "expire-on"  = "2030-12-31"
    }
  }
}

provider "mongodbatlas" {
  public_key  = var.atlas_public_key
  private_key = var.atlas_private_key
}
