# Github Action to run terraform and terragrunt

> Note: As of October 2025 this composite action uses [tofuutils/tenv](https://github.com/tofuutils/tenv) under the hood to install Terraform and Terragrunt binaries (replacing the previous `hashicorp/setup-terraform` and `autero1/action-terragrunt` actions). No changes to the input interface are required; specify `terraform-version` / `terragrunt-version` as before.

## Examples

### Run terraform without terragrunt

Common minimal workflow example. Leave `terraform-version` blank to let tenv auto-detect from `.terraform-version` or `.tool-versions`.

```yaml
name: Terraform Plan (no terragrunt)

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.terraform-version'

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform-plan:
    name: TF run
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v5
      - name: run terraform
        uses: datadrivers/terragrunt-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}            # optional but avoids API rate limits when calling github API for tools installation
          terraform-version: ""
          use-aws-auth: "true"
          aws-region: ${{ var.AWS_REGION }}
          aws-role-to-assume: ${{ var.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          cache-tenv-tools: "true" # optional, default true
          terraform-working-directory: "terraform/"  # optional, defaults to root of repo
          commands: |
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


# Use ENV vars to configure parameters for steps
env:
  AWS_REGION: "eu-central-1"
  ACCOUNT: project-dev
  CONFIG_PATH: terraform/project                            # used in custom scripts
  AWS_ROLE_TO_ASSUME: ${{ secrets.AWS_ROLE_TERRAFORM }}
  TERRAGRUNT_PARALLELISM: 4                                 # limit CPU usage

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform-validate:
    name: TF code in project-dev
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v5
      - name: Set terra*_version variables from files
        run: |
          TF_VER=$(cat .terraform-version)
          TG_VER=$(cat .terragrunt-version)
          echo "TERRAFORM_VERSION=$TF_VER" >> $GITHUB_ENV
          echo "TERRAGRUNT_VERSION=$TG_VER" >> $GITHUB_ENV
      - name: run terraform
        uses: datadrivers/terragrunt-action@v1
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          terragrunt-download: "$HOME/.terragrunt-cache/${{ env.ACCOUNT }}"
          skip-caches: "false"
          commands: |
            scripts/terragrunt/run_terragrunt run --all -- init
            scripts/terragrunt/run_terragrunt run --all -- plan -out terraform.tfplan
```

### Run terraform validate and plan via terragrunt

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v1
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          commands: |
            terragrunt run --all -- validate
            terragrunt run --all -- plan
```

### Run terraform plan via terragrunt and gcloud auth

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v1
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-gcloud-auth: "true"
          gcp-workload-identity-provider: "projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
          gcp-service-account-email: "automation-github@project-id.iam.gserviceaccount.com"
          gcp-project-id: "123456789"
          skip-caches: "false"
          commands: |
            terragrunt run --all -- plan
```

### Run terraform and create pr comment for plan on pull_request

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v1
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ env.AWS_ROLE_TO_ASSUME }}
          skip-caches: "false"
          enable-terraform-change-pr-commenter: ${{ github.event_name == 'pull_request' }}
          terraform-plan-filename: terraform.tfplan
          commands: |
            terraform init
            terraform plan -out terraform.tfplan
```

## tenv tool version caching

To avoid downloading the same Terraform / Terragrunt / OpenTofu versions on every workflow run you can enable caching of tenv managed tool directories. This is on by default.

Input: `cache-tenv-tools` (default `true`). Set to `false` to skip caching.

What is cached:

```text
~/.tenv/Terraform
~/.tenv/Terragrunt
~/.tenv/OpenTofu
```

Cache key components:

* OS (`runner.os`)
* Hash of local version indicator files (`.terraform-version`, `.terragrunt-version`, `.opentofu-version`, `terragrunt.hcl`, `root.hcl`)
* Explicit input versions (`terraform-version`, `terragrunt-version`, `tenv-version`)

Force a cache refresh by:

* Bumping any of the version files or input version values
* Adding a dummy change to e.g. `root.hcl` when using constraint based detection

Disable all caches (plugin, terragrunt download dir, tenv tool versions) via `skip-caches: "false"` (set to `true` to skip).
