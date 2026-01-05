# Minimal terraform config for stack-a
data "aws_region" "current" {}

output "region" {
  value = data.aws_region.current.name
}
