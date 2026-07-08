terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 1.2, <= 2.9.0"
    }
  }
  required_version = ">= 1.9.0"
}
