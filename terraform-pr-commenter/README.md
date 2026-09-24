# Terraform Plan PR Commenter

Converts Terraform or Terragrunt plan files to JSON and posts a pull request comment using [`liatrio/terraform-change-pr-commenter`](https://github.com/liatrio/terraform-change-pr-commenter).

## Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `terraform-plan-filename` | Plan filename to find | No | `terraform.tfplan` |
| `use-automatic-binary-detection` | Detect Terraform or OpenTofu automatically | No | `true` |
| `enable-debug` | Enable shell tracing | No | `false` |
| `include-plan-job-summary` | Add the plan to the GitHub job summary | No | `true` |
| `include-workflow-link` | Add a workflow link to the PR comment | No | `true` |
| `pr-commenter-comment-header` | PR comment heading | No | `Terraform Plan Changes` |
| `pr-commenter-comment-footer` | Text to append to the PR comment | No | (empty) |
| `continue-on-error` | Continue if posting the comment fails | No | `true` |
| `hide-previous-comments` | Hide earlier comments from this action | No | `true` |
| `log-changed-resources` | List changed resources in the PR comment | No | `true` |
| `github-token` | Token used to post the PR comment | No | `${{ github.token }}` |
| `working-directory` | Directory to search for plan files | No | `.` |

## Outputs

| Output | Description |
| --- | --- |
| `terraform_planfiles_json` | Newline-separated paths to the generated plan JSON files |
| `plan_changes_summary` | JSON counts for `create`, `update`, `delete`, `replace`, `read`, and `total` |
| `plan_changes_create` | Resources to create |
| `plan_changes_update` | Resources to update |
| `plan_changes_delete` | Resources to delete |
| `plan_changes_replace` | Resources to replace, counted separately from creates and deletes |
| `plan_changes_read` | Data sources to read |
| `plan_changes_total` | Total changes, excluding reads and no-op resources |

Counts are aggregated across all found plan files and printed in step logs. Replacements count as one change. If no plan files are found, the counts are zero.

## Usage

Generate a plan before running this action. The action searches the working directory for files matching `terraform-plan-filename`.

```yaml
permissions:
  contents: read
  pull-requests: write

steps:
  - name: Create plan
    run: terraform plan -out terraform.tfplan

  - name: Comment on plan
    id: plan
    uses: datadrivers/terragrunt-action/terraform-pr-commenter@v1
    with:
      github-token: ${{ secrets.GITHUB_TOKEN }}

  - name: Show plan counts
    env:
      PLAN_CHANGES: ${{ steps.plan.outputs.plan_changes_summary }}
    run: echo "$PLAN_CHANGES"
```

## Binary detection

With `use-automatic-binary-detection` enabled, the action uses Terragrunt when a plan's directory contains `terragrunt.hcl`. It selects Terraform or OpenTofu using `TG_TF_PATH`, version files (`.terraform-version`, `.opentofu-version`, or `.tool-versions`), or an available binary on `PATH`.

## Requirements

- A Terraform or Terragrunt plan file must exist in `working-directory`.
- The runner must have Terraform, OpenTofu, or Terragrunt available as required by the plan.
- The workflow needs `contents: read` and `pull-requests: write` permissions to post a PR comment.
