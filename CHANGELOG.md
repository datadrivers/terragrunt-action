## [4.1.1](https://github.com/datadrivers/terragrunt-action/compare/v4.1.0...v4.1.1) (2026-02-09)


### Bug Fixes

* **terragrunt:** do not skip auto-init ([#68](https://github.com/datadrivers/terragrunt-action/issues/68)) ([2ee75ac](https://github.com/datadrivers/terragrunt-action/commit/2ee75ac13a39b33756ecba20d9fb20ee9f648448))

# [4.1.0](https://github.com/datadrivers/terragrunt-action/compare/v4.0.3...v4.1.0) (2026-02-04)


### Features

* terragrunt may create plan file in different directories ([#66](https://github.com/datadrivers/terragrunt-action/issues/66)) ([2f0aadc](https://github.com/datadrivers/terragrunt-action/commit/2f0aadc7e7741b7f955c4201f607987944b7d81a))

## [4.0.3](https://github.com/datadrivers/terragrunt-action/compare/v4.0.2...v4.0.3) (2026-01-05)


### Bug Fixes

* scope hash generation to working dir ([#65](https://github.com/datadrivers/terragrunt-action/issues/65)) ([48c4e7a](https://github.com/datadrivers/terragrunt-action/commit/48c4e7a9441938c453ef75afbf5fe6396bd76dbb))

## [4.0.2](https://github.com/datadrivers/terragrunt-action/compare/v4.0.1...v4.0.2) (2025-12-22)


### Bug Fixes

* mitigate TF plugin cache bloat ([52f48af](https://github.com/datadrivers/terragrunt-action/commit/52f48af77f474a8aea800c00e466114d9fc8e12e))

## [4.0.1](https://github.com/datadrivers/terragrunt-action/compare/v4.0.0...v4.0.1) (2025-12-08)


### Bug Fixes

* build cache path based on inputs ([a173c73](https://github.com/datadrivers/terragrunt-action/commit/a173c7384b3f894941b4515c8b0e594b45d03fb9))

# [4.0.0](https://github.com/datadrivers/terragrunt-action/compare/v3.0.0...v4.0.0) (2025-11-27)


* feat!: split pr-commenter into sub action ([#61](https://github.com/datadrivers/terragrunt-action/issues/61)) ([e752434](https://github.com/datadrivers/terragrunt-action/commit/e7524344e1370c8dc379deaf0b1bb0da59a502a4))


### BREAKING CHANGES

* pr commenter removed into separate action

Signed-off-by: Steffen Tautenhahn <stevie-@users.noreply.github.com>

# [3.0.0](https://github.com/datadrivers/terragrunt-action/compare/v2.2.2...v3.0.0) (2025-11-25)


* feat!: change github token logic ([#60](https://github.com/datadrivers/terragrunt-action/issues/60)) ([954b3d1](https://github.com/datadrivers/terragrunt-action/commit/954b3d1e2608868b2fd3b69aaef61b7f026ca926))


### BREAKING CHANGES

* removed input github-token

Signed-off-by: Steffen Tautenhahn <stevie-@users.noreply.github.com>

## [2.2.2](https://github.com/datadrivers/terragrunt-action/compare/v2.2.1...v2.2.2) (2025-11-19)


### Bug Fixes

* let curl retry rate limit errors ([e3e24b4](https://github.com/datadrivers/terragrunt-action/commit/e3e24b4cd0dc9f70bcd52b5a3bc460373d283e38))

## [2.2.1](https://github.com/datadrivers/terragrunt-action/compare/v2.2.0...v2.2.1) (2025-11-08)


### Bug Fixes

* **tenv:** find action resources ([d25655e](https://github.com/datadrivers/terragrunt-action/commit/d25655ed82587d02c8dafbfd85c231d2e0de0354))
* **tenv:** reuse tool install cache ([aeced4e](https://github.com/datadrivers/terragrunt-action/commit/aeced4e2febe845d326e3b3dc003cf0f118597f7))

# [2.2.0](https://github.com/datadrivers/terragrunt-action/compare/v2.1.1...v2.2.0) (2025-11-07)


### Features

* **tenv:** add tenv tool caching ([#55](https://github.com/datadrivers/terragrunt-action/issues/55)) ([20bf64f](https://github.com/datadrivers/terragrunt-action/commit/20bf64f887e69eed2ccbdaff37cc62694b49aff1))

## [2.1.1](https://github.com/datadrivers/terragrunt-action/compare/v2.1.0...v2.1.1) (2025-10-17)


### Bug Fixes

* parallel runs may cause the api to rate limit ([81b30b9](https://github.com/datadrivers/terragrunt-action/commit/81b30b96cd1556a94ca0edfc422f16a6f6d52ef4))

# [2.1.0](https://github.com/datadrivers/terragrunt-action/compare/v2.0.1...v2.1.0) (2025-10-03)


### Features

* **setup:** introduce tenv as version manager ([f42610e](https://github.com/datadrivers/terragrunt-action/commit/f42610eb46d2884645815db329e0265da206ca02))

## [2.0.1](https://github.com/datadrivers/terragrunt-action/compare/v2.0.0...v2.0.1) (2025-09-24)


### Bug Fixes

* **terragrunt:** fix ENV var name ([4280278](https://github.com/datadrivers/terragrunt-action/commit/42802783e65620a776341abe841eec0f9309d48e))

# [2.0.0](https://github.com/datadrivers/terragrunt-action/compare/v1.7.0...v2.0.0) (2025-09-24)


* feat!: remove ssh-agent ([62143ce](https://github.com/datadrivers/terragrunt-action/commit/62143ce38ccad02314616e4c106c51de415336d2))


### BREAKING CHANGES

* removed ssh-agent

Signed-off-by: Steffen Tautenhahn <stevie-@users.noreply.github.com>

# [1.7.0](https://github.com/datadrivers/terragrunt-action/compare/v1.6.0...v1.7.0) (2025-09-09)


### Features

* release new version ([5b1773e](https://github.com/datadrivers/terragrunt-action/commit/5b1773e15be18252dc27ab30f24e4b9028697cad))

# [1.6.0](https://github.com/datadrivers/terragrunt-action/compare/v1.5.4...v1.6.0) (2025-07-07)


### Features

* **deps:** bump the github-actions group with 2 updates ([#46](https://github.com/datadrivers/terragrunt-action/issues/46)) ([4aa7c74](https://github.com/datadrivers/terragrunt-action/commit/4aa7c7433659a6e8edf507551be58c19d890b081))

## [1.5.4](https://github.com/datadrivers/terragrunt-action/compare/v1.5.3...v1.5.4) (2025-06-10)


### Bug Fixes

* **deps:** bump the github-actions group across 1 directory with 2 updates ([#43](https://github.com/datadrivers/terragrunt-action/issues/43)) ([666301e](https://github.com/datadrivers/terragrunt-action/commit/666301ec4034d0c424912922d52e9b206c034729))

## [1.5.3](https://github.com/datadrivers/terragrunt-action/compare/v1.5.2...v1.5.3) (2025-03-24)


### Bug Fixes

* **deps:** bump the github-actions group across 1 directory with 2 updates ([#41](https://github.com/datadrivers/terragrunt-action/issues/41)) ([48fb17f](https://github.com/datadrivers/terragrunt-action/commit/48fb17f5cbfc7c40e5ccccf93714f11ebf65494a))

## [1.5.2](https://github.com/datadrivers/terragrunt-action/compare/v1.5.1...v1.5.2) (2025-02-27)


### Bug Fixes

* versions.tf changes update plugin cache ([973bba7](https://github.com/datadrivers/terragrunt-action/commit/973bba7885588c16d5e4a41efc53d6afe20027eb))

## [1.5.1](https://github.com/datadrivers/terragrunt-action/compare/v1.5.0...v1.5.1) (2024-12-16)


### Bug Fixes

* **deps:** bump liatrio/terraform-change-pr-commenter ([#38](https://github.com/datadrivers/terragrunt-action/issues/38)) ([4c1a6cb](https://github.com/datadrivers/terragrunt-action/commit/4c1a6cbc23d493755f905db41fab2024fc935252))

# [1.5.0](https://github.com/datadrivers/terragrunt-action/compare/v1.4.0...v1.5.0) (2024-09-04)


### Features

* pr-commenter doesn't show json output in log ([0763f63](https://github.com/datadrivers/terragrunt-action/commit/0763f632b6a38f796d92f7d1acc05a292f556dc1))

# [1.4.0](https://github.com/datadrivers/terragrunt-action/compare/v1.3.0...v1.4.0) (2024-08-20)


### Features

* improve cache hits ([#35](https://github.com/datadrivers/terragrunt-action/issues/35)) ([6d67c9b](https://github.com/datadrivers/terragrunt-action/commit/6d67c9b99e3970db926a89e8ed068815292b5bdc))

# [1.3.0](https://github.com/datadrivers/terragrunt-action/compare/v1.2.0...v1.3.0) (2024-07-10)


### Features

* **pr-commenter:** allow to overwrite comment header/footer ([#34](https://github.com/datadrivers/terragrunt-action/issues/34)) ([71ea252](https://github.com/datadrivers/terragrunt-action/commit/71ea25268ffdeed5e156031de987e696665fea3a))

# [1.2.0](https://github.com/datadrivers/terragrunt-action/compare/v1.1.2...v1.2.0) (2024-05-13)


### Features

* **deps:** bump liatrio/terraform-change-pr-commenter ([#33](https://github.com/datadrivers/terragrunt-action/issues/33)) ([6bb3c6d](https://github.com/datadrivers/terragrunt-action/commit/6bb3c6d43259d0a7493bd25b83218476167b0971))

## [1.1.2](https://github.com/datadrivers/terragrunt-action/compare/v1.1.1...v1.1.2) (2024-03-04)


### Bug Fixes

* trigger semantic release ([522e04c](https://github.com/datadrivers/terragrunt-action/commit/522e04cc528df9f38e6af63ac97883d6dc7fefd4))

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
