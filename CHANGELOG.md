## v1.1.1 (2024-02-23)

### Fix

- make aws auth optional

## v1 (2024-02-19)

## v1.1.0 (2024-02-19)

### Feat

- upgrade dependency to nodejs20

## v1.0.0 (2024-02-09)

### BREAKING CHANGE

- `terragrunt-command` is renamed to `commands`
- removed parameter `terragrunt-download-cache-target` which is
replaced by `terragrunt-download`

### Feat

- renamed parameter for commands

## v0 (2024-02-09)

### Feat

- upgrade nodejs actions

## v0.12.0 (2024-02-09)

### Feat

- upgrade nodejs actions

## v0.11.3 (2024-02-05)

### Fix

- nodejs update

## v0.11.2 (2024-02-02)

### Fix

- nodejs update

## v0 (2024-01-29)

### Fix

- upgrade action versions

## v0.11.1 (2024-01-29)

### Fix

- upgrade action versions

## v0.11.0 (2024-01-10)

### Feat

- add toggle to disable automatic binary detection (#23)

## v0.10.3 (2023-08-24)

### Fix

- version upgrades

## v0.10.2 (2023-03-14)

### Fix

- use latest aws auth action

## v0.10.1 (2023-02-13)

### Fix

- nodejs deprecation warning

## v0.10.0 (2023-01-24)

### Feat

- **terragrunt**: use token for higher api rate limits (#17)

## v0.9.0 (2023-01-13)

### Feat

- terragrunt cache dir and job summary (#16)
- **gcloud-auth**: use latest version

## v0.8.0 (2022-11-15)

### Feat

- **gcloud-auth**: use latest version

## v0.7.4 (2022-11-09)

### Fix

- Removes nodejs 12 warning (#14)

## v0.7.3 (2022-10-24)

## v0.7.2 (2022-10-17)

### Fix

- need rng delimiter for multiline output (#12)

## v0.7.1 (2022-10-17)

### Fix

- remove deprecated set-output call

## v0.7.0 (2022-06-15)

### Feat

- **self-hosted**: clean up cache dirs

## v0.6.1 (2022-06-09)

### Fix

- **pr-commenter**: commenter doesn't fail on empty changes (#8)

## v0.6.0 (2022-06-09)

### Feat

- speed up convert of plans (#6)

## v0.5.0 (2022-06-08)

### Feat

- **action**: skip pr action on empty input (#5)

## v0.4.2 (2022-06-08)

## v0.4.1 (2022-06-08)

### Fix

- **pr-comment**: do not fail job if pr comment failed

## v0.4.0 (2022-06-08)

### Feat

- **test**: test multiple files (#4)
- **debug**: add debug option
- **terraform**: test terragrunt (#3)
- **terraform**: add comment for terraform plan with test (#2)

### Fix

- **terraform**: correct path switch in loop
- **terraform**: use real path to output json
- **terraform**: replace basename to get filename
- **terraform**: correct parameter evaluation
- **terraform**: check for terragrunt

## v0 (2022-05-06)

### Feat

- **github**: update actions to latest versions

## v0.2.1 (2022-02-23)

### Fix

- latest is not a valid version for installers

## v0.2.0 (2022-02-18)

## v0.1.0 (2022-02-04)

### Feat

- **pipeline**: initial action
