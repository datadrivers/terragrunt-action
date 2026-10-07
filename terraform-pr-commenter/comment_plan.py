import os
import sys
from typing import Optional

from commenter import run_commenter, options_from_environment
from commenter_types import CommenterError
from github_api import GitHubApi


def run() -> None:
    options = options_from_environment(os.environ)
    api: Optional[GitHubApi] = None
    if options.pull_request is not None:
        api = GitHubApi.from_environment(os.environ)
    run_commenter(options, api)


if __name__ == "__main__":
    try:
        run()
    except CommenterError as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
