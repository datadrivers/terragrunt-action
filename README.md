# Github Action to run terraform and terragrunt

## Examples

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


# Use ENV vars to configure parameters for steps
env:
  AWS_REGION: "eu-central-1"
  ACCOUNT: project-dev
  CONFIG_PATH: terraform/project                            # used in costum scripts
  AWS_ROLE_TO_ASSUME: ${{ secrets.AWS_ROLE_TERRAFORM_DEV }}
  TERRAGRUNT_PARALLELISM: 4                                 # limit CPU usage

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform-validate:
    name: TF code in project-dev
    runs-on: ubuntu-18.04
    steps:
      - uses: actions/checkout@v3
      - name: Set terra*_version variables from files
        run: |
          TF_VER=$(cat .terraform-version)
          TG_VER=$(cat .terragrunt-version)
          echo "TERRAFORM_VERSION=$TF_VER" >> $GITHUB_ENV
          echo "TERRAGRUNT_VERSION=$TG_VER" >> $GITHUB_ENV
      - name: run terraform
        uses: datadrivers/terragrunt-action@v0
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

### Run terraform validate and plan via terragrunt

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v0
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
        uses: datadrivers/terragrunt-action@v0
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-gcloud-auth: "true"
          gcp-workload-identity-provider: "projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
          gcp-service-account-email: "automation-github@project-id.iam.gserviceaccount.com"
          gcp-project-id: "123456789"
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            terragrunt run-all plan
```

### Run terraform without terragrunt

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v0
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          use-ssh-agent: "true"
          ssh-private-key: ${{ secrets.GIT_SSH_PRIVATE_KEY }}
          terragrunt-command: |
            terraform plan
```

### Run terraform and create pr comment for plan on pull_request

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v0
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          enable-terraform-change-pr-commenter: ${{ github.event_name == 'pull_request' }}
          terraform-plan-filename: terraform.tfplan
          terragrunt-command: |
            terraform init
            terraform plan -out terraform.tfplan
```
