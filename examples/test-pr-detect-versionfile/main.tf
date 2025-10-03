resource "local_file" "txt" {
  content         = "Lorem Ipsum"
  filename        = format("%s.txt", var.filename)
  file_permission = "0644"
}
