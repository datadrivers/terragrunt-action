# Developer Guidelines

- [Developer Guidelines](#developer-guidelines)
  - [Contribute](#contribute)
  - [Create release](#create-release)
    - [semver release](#semver-release)
    - [Github market place release](#github-market-place-release)
    - [Move major version tag](#move-major-version-tag)

## Contribute

1. Please contribute via feature branches
2. Create an [example](./examples) code and [test coverage](./github/workflows/test.yml) if not already covered
3. Create PR to run tests
4. Merge after approval

## Create release

### semver release

```bash
# check if release can be created
cz bump --changelog --dry-run
## if cz detects no change, check if commit messages are correct

# create new release and changelog update
cz bump --changelog

# push release and tag
git push && git push --tags
```

After this we can make an marketplace release via github

### Github market place release

1. go to [Draft a new Release on github releases page](https://github.com/datadrivers/terragrunt-action/releases/new)
2. Select latest tag on `Choose a tag` Button
3. Click on `Generate release notes`
4. Check generated release notes if they contain a `## What's Changed` section. If not add one similar to the old releases
5. Click on `Publish release`

### Move major version tag

make sure you have create a semver release before moving major version tag, since changelog will be broken if order is wrong.

```bash
# we need force since we overwrite existing tag
git tag v1 --force
git push --tags --force
```
