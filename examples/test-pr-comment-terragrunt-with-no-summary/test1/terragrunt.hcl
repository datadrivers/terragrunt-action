terraform {
  source = "${get_repo_root()}/examples//test-pr-comment"

  extra_arguments "plan_args" {
    commands = ["plan"]
    arguments = concat(
      [
        "-lock=false" # do not lock on plan - useful in CI to use plan to validate code
      ],
      tobool(get_env("CI", "false")) ? ["-out", "${get_terragrunt_dir()}/terraform.tfplan"] : [] # in github actions autogenerate plan into terragrunt dir
    )
  }
}

inputs = {
    filename = "test1"
}
