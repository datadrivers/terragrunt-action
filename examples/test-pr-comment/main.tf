resource "local_file" "test" {
  content         = "Lorem Ipsum"
  filename        = "test.txt"
  file_permission = "0644"
}
