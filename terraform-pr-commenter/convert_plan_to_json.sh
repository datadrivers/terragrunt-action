#!/usr/bin/env bash
set -euo pipefail

# Convert terraform plan files to json and emit GITHUB_OUTPUT variable
INPUT_TERRAFORM_PLAN_FILENAME="${INPUT_TERRAFORM_PLAN_FILENAME:-terraform.tfplan}"
INPUT_USE_AUTOMATIC_BINARY_DETECTION="${INPUT_USE_AUTOMATIC_BINARY_DETECTION:-true}"
INPUT_ENABLE_DEBUG="${INPUT_ENABLE_DEBUG:-false}"

[[ "${INPUT_ENABLE_DEBUG}" == "true" ]] && set -x

echo "::group::convert terraform plan files to json"
planfiles_json=()

tf_convert_plan_to_json(){
  local planfile="$1"
  exec 3>&1
  exec 1>&2
  planfile_name=$(basename "${planfile}")
  planfile_path=$(dirname "${planfile}")
  terraform_bin="terraform"
  tfplan_json=$(readlink -f "${planfile_path}/tfplan.json")
  pushd "${planfile_path}" >/dev/null
  if [[ "${INPUT_USE_AUTOMATIC_BINARY_DETECTION}" == "true" && -s terragrunt.hcl ]]; then
    terraform_bin="terragrunt"
  fi
  "$terraform_bin" show -no-color -json "${planfile_name}" > "${tfplan_json}"
  popd >/dev/null
  echo "${tfplan_json}" >&3
}

while IFS= read -r -d '' file; do
  planfiles_json+=("$(tf_convert_plan_to_json "$file")")
done < <(find . -type f -name "${INPUT_TERRAFORM_PLAN_FILENAME}" -print0)

content="$(printf "%s\n" "${planfiles_json[@]}")"
if [[ -n "${content// /}" ]]; then
  delimiter="$(openssl rand -hex 8)"
  printf 'terraform_planfiles_json<<%s\n%s\n%s\n' "$delimiter" "$content" "$delimiter" >> "$GITHUB_OUTPUT"
fi
echo "::endgroup::"
