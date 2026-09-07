# Broken JSON commenter fixture

This directory is used by the workflow test for malformed Terraform plan JSON.
The test replaces Terraform with a small command that emits invalid JSON for
`terraform show -json`.
