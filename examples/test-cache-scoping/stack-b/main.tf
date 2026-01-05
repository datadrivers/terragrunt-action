# Minimal terraform config for stack-b
data "aws_region" "current" {}

output "region" {
  value = data.aws_region.current.name
}
