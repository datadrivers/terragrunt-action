#!/usr/bin/env bash
set -euo pipefail

# Convert terraform plan files to json and emit GITHUB_OUTPUT variable
INPUT_TERRAFORM_PLAN_FILENAME="${INPUT_TERRAFORM_PLAN_FILENAME:-terraform.tfplan}"
INPUT_USE_AUTOMATIC_BINARY_DETECTION="${INPUT_USE_AUTOMATIC_BINARY_DETECTION:-true}"
INPUT_ENABLE_DEBUG="${INPUT_ENABLE_DEBUG:-false}"

[[ "${INPUT_ENABLE_DEBUG}" == "true" ]] && set -x

echo "::group::convert terraform plan files to json"
planfiles_json=()

detect_terraform_binary(){
  local directory="$1"
  local configured_binary="${TG_TF_PATH:-}"
  local current_directory="$directory"

  if [[ -n "${configured_binary}" ]]; then
    printf '%s\n' "${configured_binary}"
    return
  fi

  while [[ "${current_directory}" != "/" ]]; do
    if [[ -f "${current_directory}/.opentofu-version" ]] ||
      [[ -f "${current_directory}/.tool-versions" ]] &&
      grep -Eq '^[[:space:]]*(tofu|opentofu)([[:space:]]|$)' "${current_directory}/.tool-versions"; then
      printf '%s\n' "tofu"
      return
    fi
    if [[ -f "${current_directory}/.terraform-version" ]] ||
      [[ -f "${current_directory}/.tool-versions" ]] &&
      grep -Eq '^[[:space:]]*terraform([[:space:]]|$)' "${current_directory}/.tool-versions"; then
      printf '%s\n' "terraform"
      return
    fi
    current_directory="$(dirname "${current_directory}")"
  done

  if command -v terraform >/dev/null 2>&1; then
    printf '%s\n' "terraform"
  elif command -v tofu >/dev/null 2>&1; then
    printf '%s\n' "tofu"
  else
    echo "::error::Could not detect a Terraform or OpenTofu binary" >&2
    return 1
  fi
}

tf_convert_plan_to_json(){
  local planfile="$1"
  local terraform_bin="terraform"
  local terraform_path=""
  exec 3>&1
  exec 1>&2
  local planfile_name
  local planfile_path
  local tfplan_json
  planfile_name="$(basename "${planfile}")"
  planfile_path="$(dirname "${planfile}")"
  tfplan_json="$(readlink -f "${planfile_path}/tfplan.json")"
  pushd "${planfile_path}" >/dev/null
  if [[ "${INPUT_USE_AUTOMATIC_BINARY_DETECTION}" == "true" && -s terragrunt.hcl ]]; then
    terraform_bin="terragrunt"
    terraform_path="$(detect_terraform_binary "${PWD}")"
  elif [[ "${INPUT_USE_AUTOMATIC_BINARY_DETECTION}" == "true" ]]; then
    terraform_bin="$(detect_terraform_binary "${PWD}")"
  fi
  if [[ "${terraform_bin}" == "terragrunt" ]]; then
    TG_TF_PATH="${terraform_path}" "$terraform_bin" show -no-color -json "${planfile_name}" > "${tfplan_json}"
  else
    "$terraform_bin" show -no-color -json "${planfile_name}" > "${tfplan_json}"
  fi
  if ! jq empty "${tfplan_json}" >/dev/null 2>&1; then
    echo "::error file=${tfplan_json}::Generated Terraform plan JSON is invalid; showing the first 40 lines" >&2
    sed -n '1,40p' "${tfplan_json}" >&2
    return 1
  fi
  popd >/dev/null
  echo "${tfplan_json}" >&3
}

export -f tf_convert_plan_to_json
export -f detect_terraform_binary
export INPUT_USE_AUTOMATIC_BINARY_DETECTION

# Run conversions in parallel
tmp_output=$(mktemp)
trap "rm -f $tmp_output" EXIT

set +e
find . -type f -name "${INPUT_TERRAFORM_PLAN_FILENAME}" -print0 | \
  xargs -0 -P "$(nproc)" -I {} bash -c 'tf_convert_plan_to_json "$@" >> '"$tmp_output" _ {}
conversion_exit_code=$?
set -e
if [[ "${conversion_exit_code}" -ne 0 ]]; then
  exit "${conversion_exit_code}"
fi

# Collect results from parallel execution
if [[ -s "$tmp_output" ]]; then
  mapfile -t planfiles_json < "$tmp_output"
fi

content="$(printf "%s\n" "${planfiles_json[@]}")"
if [[ -n "${content// /}" ]]; then
  delimiter="$(openssl rand -hex 8)"
  printf 'terraform_planfiles_json<<%s\n%s\n%s\n' "$delimiter" "$content" "$delimiter" >> "$GITHUB_OUTPUT"
fi
echo "::endgroup::"
