# Test PR Comment with Working Directory Override

This example tests the `working-directory` input parameter of the terraform-pr-commenter action.

## Structure

- `root/` - Terraform configuration in a subdirectory
  - `main.tf` - Simple AWS resource configuration
  - `versions.tf` - Provider configuration
  - `variables.tf` - Variable definitions

The test verifies that the action correctly:

1. Changes to the specified `working-directory` before processing
2. Finds and converts the plan file in the specified directory
3. Posts PR comments based on plans created in subdirectories

## Usage

```yaml
- name: Run terraform plan
  working-directory: root
  run: |
    terraform init
    terraform plan -out terraform.tfplan

- name: Add PR comment for terraform plan
  uses: datadrivers/terragrunt-action/terraform-pr-commenter@v4
  with:
    terraform-plan-filename: terraform.tfplan
    working-directory: root
```
