# Github Action to run terraform and terragrunt

## Examples

### Run terraform validate and plan via terragrunt

```yaml
      - name: run terraform
        uses: ./.github/actions/run-terragrunt
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            terragrunt run-all validate
            terragrunt run-all plan
```

### Run terraform plan via terragrunt and gcloud auth

```yaml
      - name: run terraform
        uses: ./.github/actions/run-terragrunt
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-gcloud-auth: "true"
          gcp-workload-identity-provider: "projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
          gcp-service-account-email: "automation-github@project-id.iam.gserviceaccount.com"
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            terragrunt run-all plan
```

### Run terraform without terragrunt

```yaml
      - name: run terraform
        uses: ./.github/actions/run-terragrunt
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            terraform plan
```

### Complete workflow with custom scripts to run terraform plan via terragrunt

```yaml
name: Terraform Validate dev

on:
  pull_request:
    paths:
      - ".terra*-version"
      - "terraform/**"
    branches:
      - develop

defaults:
  run:
    shell: bash

env:
  AWS_REGION: "eu-central-1"
  ACCOUNT: project-dev
  CONFIG_PATH: terraform/project
  AWS_ROLE_TO_ASSUME: ${{ secrets.AWS_ROLE_TERRAFORM_DEV }}
  TERRAGRUNT_PARALLELISM: 4 # limit CPU usage

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform-validate:
    name: TF code in project-dev
    runs-on: ubuntu-18.04
    steps:
      - uses: actions/checkout@v2
      - name: Set variables
        run: |
          TF_VER=$(cat .terraform-version)
          TG_VER=$(cat .terragrunt-version)
          echo "TERRAFORM_VERSION=$TF_VER" >> $GITHUB_ENV
          echo "TERRAGRUNT_VERSION=$TG_VER" >> $GITHUB_ENV
      - name: run terraform
        uses: ./.github/actions/run-terragrunt
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          terragrunt-download-cache-target: ${{ env.ACCOUNT }}
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            scripts/terragrunt/init_terraform_plugins.sh
            scripts/terragrunt/run_terragrunt run-all plan -out terraform.tfplan
```
