# This is dummy terragrunt.hcl file.

generate "demo" {
  path      = "main.tf"
  if_exists = "overwrite"
  contents  = <<EOF
resource "local_file" "txt" {
  content         = "Lorem Ipsum"
  filename        = format("%s.txt", var.filename)
  file_permission = "0644"
}
EOF
}
