# Github Action to run terraform and terragrunt

> Note: As of October 2025 this composite action uses [tofuutils/tenv](https://github.com/tofuutils/tenv) under the hood to install Terraform and Terragrunt binaries (replacing the previous `hashicorp/setup-terraform` and `autero1/action-terragrunt` actions). No changes to the input interface are required; specify `terraform-version` / `terragrunt-version` as before.
> Set TENV_GITHUB_TOKEN environment variable to ${{ github.token }} for tenv API calls to github (e.g. to avoid rate limits).

## Examples

### Run terraform (without terragrunt)

Common minimal workflow example. Leave `terraform-version` blank to let tenv auto-detect from `.terraform-version` or `.tool-versions`.

```yaml
name: Terraform Plan (no terragrunt)

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.terraform-version'

permissions: {}

jobs:
  terraform-plan:
    runs-on: ubuntu-24.04
    permissions:
      id-token: write       # for OIDC auth
      contents: read
      pull-requests: write  # for PR commenter
    steps:
      - uses: actions/checkout@v6
      - name: install terraform
        uses: datadrivers/terragrunt-action@v4
        env:
          TENV_GITHUB_TOKEN: ${{ github.token }}   # optional but avoids API rate limits when calling github API for tools installation
        with:
          terraform-version: ""
          use-aws-auth: "true"
          aws-region: ${{ var.AWS_REGION }}
          aws-role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}
      - name: run terraform
        working-directory: "terraform/"
        run: |
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
  TERRAGRUNT_PARALLELISM: 4          # limit CPU usage

permissions: {}

jobs:
  terraform-validate:
    name: TF code in project-dev
    runs-on: ubuntu-24.04
    permissions:
      id-token: write       # for OIDC auth
      contents: read
      pull-requests: write  # for PR commenter
    steps:
      - uses: actions/checkout@v6
      - name: Set terra*_version variables from files
        run: |
          TF_VER=$(cat .terraform-version)
          TG_VER=$(cat .terragrunt-version)
          echo "TERRAFORM_VERSION=$TF_VER" >> $GITHUB_ENV
          echo "TERRAGRUNT_VERSION=$TG_VER" >> $GITHUB_ENV
      - name: run terraform
        uses: datadrivers/terragrunt-action@v4
        env:
          TENV_GITHUB_TOKEN: ${{ github.token }}   # optional but avoids API rate limits when calling github API for tools installation
        with:
          terraform-version: ${{ env.TERRAFORM_VERSION }}
          terragrunt-version: ${{ env.TERRAGRUNT_VERSION }}
          use-aws-auth: "true"
          aws-region: ${{ env.AWS_REGION }}
          aws-role-to-assume: ${{ secrets.AWS_ROLE_TERRAFORM }}
          terragrunt-download: "$HOME/.terragrunt-cache/${{ env.ACCOUNT }}"
          skip-caches: "false"
          commands: |
            terragrunt run --all -- init
            terragrunt run --all -- plan -out terraform.tfplan
```

### Run terraform validate and plan via terragrunt

```yaml
      - name: run terraform
        uses: datadrivers/terragrunt-action@v4
        env:
          TENV_GITHUB_TOKEN: ${{ github.token }}   # optional but avoids API rate limits when calling github API for tools installation
        with:
          terraform-version: ""
          terragrunt-version: ""
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
        uses: datadrivers/terragrunt-action@v4
        env:
          TENV_GITHUB_TOKEN: ${{ github.token }}   # optional but avoids API rate limits when calling github API for tools installation
        with:
          terraform-version: ""
          terragrunt-version: ""
          use-gcloud-auth: "true"
          gcp-workload-identity-provider: "projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
          gcp-service-account-email: "automation-github@project-id.iam.gserviceaccount.com"
          gcp-project-id: "123456789"
          skip-caches: "false"
          commands: |
            terragrunt run --all -- plan
```

### Run terraform and create PR comment for plan on pull_request

terraform commands have to make sure to create a plan file (e.g. `terraform.tfplan`) for the PR commenter action to pick up and convert to JSON for the comment.:

```yaml
jobs:
  terraform-plan:
    runs-on: ubuntu-24.04
    permissions:
      id-token: write       # for OIDC auth
      contents: read
      pull-requests: write  # for PR commenter
    steps:
      - uses: actions/checkout@v6
      - name: install terraform
        uses: datadrivers/terragrunt-action@v4
        env:
          TENV_GITHUB_TOKEN: ${{ github.token }}
        with:
          terraform-version: ""
      - name: run terraform
        working-directory: examples/my-module
        run: |
          terraform init
          terraform plan -out terraform.tfplan
      - name: add PR comment for terraform plan
        if: ${{ github.event_name == 'pull_request' }}
        uses: datadrivers/terragrunt-action/terraform-pr-commenter@v4
        with:
          terraform-plan-filename: terraform.tfplan # default
          pr-commenter-comment-header: "Terraform Plan Changes" # default
          pr-commenter-comment-footer: "Review plan above"
          github-token: ${{ secrets.PAT_TOKEN }} # optional, uses GITHUB_TOKEN by default
```

## tenv tool version caching

To avoid downloading the same Terraform / Terragrunt / OpenTofu versions on every workflow run you can enable caching of tenv managed tool directories. This is on by default.

Input: `cache-tenv-tools` (default `true`). Set to `false` to skip caching.

What is cached:

```text
~/.tenv/Terraform/{tool version}
~/.tenv/Terragrunt/{tool version}
~/.tenv/OpenTofu
```

Cache key components:

- OS (`runner.os`)
- Hash of local version indicator files (`.terraform-version`, `.terragrunt-version`, `.opentofu-version`, `terragrunt.hcl`, `root.hcl`)
- Explicit input versions (`terraform-version`, `terragrunt-version`, `tenv-version`)

Force a cache refresh by:

- Bumping any of the version files or input version values
- Adding a dummy change to e.g. `root.hcl` when using constraint based detection

Disable all caches (plugin, terragrunt download dir, tenv tool versions) via `skip-caches: "true"` or enable them with `skip-caches: "false"` (default).
