import hashlib
import json
import os
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from commenter_types import (
    Comment,
    CommentApi,
    CommenterError,
    CommenterOptions,
    CommentPolicy,
)
from plan import PlanWithChanges, load_plans, render_comment


def input_bool(
    name: str, default: bool, environ: Mapping[str, str]
) -> bool:
    value = environ.get(name)
    if value is None or value == "":
        return default
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise CommenterError(f"{name} must be 'true' or 'false', got {value!r}")


def pull_request_number(event_name: str, event: Mapping[str, Any]) -> Optional[int]:
    if event_name not in {"pull_request", "pull_request_target", "workflow_call"}:
        return None
    pull_request = event.get("pull_request") or {}
    number = pull_request.get("number")
    if number is None and event_name == "workflow_call":
        number = event.get("number")
    if number is not None and not isinstance(number, int):
        raise CommenterError("Pull request number in the event payload must be an integer")
    return number


def options_from_environment(
    environ: Optional[Mapping[str, str]] = None,
) -> CommenterOptions:
    values = os.environ if environ is None else environ
    paths = tuple(
        path.strip()
        for path in values.get("INPUT_JSON_FILES", "").splitlines()
        if path.strip()
    )
    if not paths:
        raise CommenterError("No Terraform plan JSON files were provided")

    event: Any = {}
    event_path = values.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            with open(event_path, encoding="utf-8") as event_file:
                event = json.load(event_file)
        except OSError as error:
            raise CommenterError(
                f"Could not read GitHub event payload: {error}"
            ) from error
        except json.JSONDecodeError as error:
            raise CommenterError(f"Invalid GitHub event payload: {error}") from error
    if not isinstance(event, dict):
        raise CommenterError("GitHub event payload must be a JSON object")

    event_name = values.get("GITHUB_EVENT_NAME", "")
    repository = values.get("GITHUB_REPOSITORY", "")
    workflow_link = ""
    if input_bool("INPUT_INCLUDE_WORKFLOW_LINK", True, values):
        server_url = values.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        run_id = values.get("GITHUB_RUN_ID", "")
        workflow = values.get("GITHUB_WORKFLOW", "")
        if repository and run_id:
            workflow_link = (
                f"[Workflow: {workflow}]"
                f"({server_url}/{repository}/actions/runs/{run_id})"
            )

    return CommenterOptions(
        json_paths=paths,
        header=values.get("INPUT_COMMENT_HEADER", "Terraform Plan Changes"),
        footer=values.get("INPUT_COMMENT_FOOTER", ""),
        include_plan_job_summary=input_bool(
            "INPUT_INCLUDE_PLAN_JOB_SUMMARY", True, values
        ),
        log_changed_resources=input_bool(
            "INPUT_LOG_CHANGED_RESOURCES", True, values
        ),
        replace_existing_comments=input_bool(
            "INPUT_REPLACE_EXISTING_COMMENTS", False, values
        ),
        hide_previous_comments=input_bool(
            "INPUT_HIDE_PREVIOUS_COMMENTS", True, values
        ),
        repository=repository,
        pull_request=pull_request_number(event_name, event),
        workflow_link=workflow_link,
        step_summary_path=values.get("GITHUB_STEP_SUMMARY"),
        workspace=values.get("GITHUB_WORKSPACE"),
    )


def _stable_plan_paths(
    paths: Sequence[str], workspace: Optional[str]
) -> Tuple[str, ...]:
    normalized = set()
    workspace_path = os.path.abspath(workspace) if workspace else None
    for path in paths:
        absolute_path = os.path.abspath(path)
        if workspace_path:
            try:
                is_in_workspace = (
                    os.path.commonpath([absolute_path, workspace_path])
                    == workspace_path
                )
            except ValueError:
                is_in_workspace = False
            stable_path = (
                os.path.relpath(absolute_path, workspace_path)
                if is_in_workspace
                else os.path.normpath(path)
            )
        else:
            stable_path = os.path.normpath(path)
        normalized.add(stable_path.replace(os.sep, "/"))
    return tuple(sorted(normalized))


def comment_marker(
    repository: str,
    header: str,
    plan_paths: Sequence[str],
    workspace: Optional[str] = None,
) -> str:
    identity = json.dumps(
        [
            repository.lower(),
            header,
            _stable_plan_paths(plan_paths, workspace),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"<!-- terragrunt-action-pr-commenter:{digest} -->"


def legacy_comment_marker(repository: str, header: str) -> str:
    value = f"{repository.lower()}\0{header}".encode("utf-8")
    digest = hashlib.sha256(value).hexdigest()[:20]
    return f"<!-- terragrunt-action-pr-commenter:v1:{digest} -->"


def is_action_comment(comment: Mapping[str, Any], policy: CommentPolicy) -> bool:
    body = comment.get("body") or ""
    if policy.marker in body:
        return True

    expected_plan_lines = {
        f"{policy.header} for `{path}`" for path in policy.plan_paths
    }
    if not expected_plan_lines.intersection(body.splitlines()):
        return False
    if policy.legacy_marker in body:
        return True

    user = comment.get("user") or {}
    return (
        user.get("login") in {"github-actions", "github-actions[bot]"}
        and "<b>Terraform Plan:" in body
    )


def select_latest_comment(comments: Sequence[Comment]) -> Comment:
    return max(
        comments,
        key=lambda comment: comment.get("updated_at")
        or comment.get("created_at")
        or "",
    )


def publish_comment(
    api: CommentApi,
    repository: str,
    pull_request: int,
    body: str,
    policy: CommentPolicy,
) -> str:
    comments = api.list_issue_comments(repository, pull_request)
    matching = [
        comment for comment in comments if is_action_comment(comment, policy)
    ]

    if policy.replace_existing and matching:
        target = select_latest_comment(matching)
        api.update_comment(repository, target["id"], body)
        print(f"Updated existing PR comment {target['id']}.")
        if policy.hide_previous:
            older = [comment for comment in matching if comment["id"] != target["id"]]
            api.minimize_comments(repository, pull_request, older)
        return "updated"

    if policy.hide_previous:
        api.minimize_comments(repository, pull_request, matching)
    api.create_comment(repository, pull_request, body)
    print("Created a PR comment.")
    return "created"


def append_job_summary(body: str, summary_path: Optional[str]) -> None:
    if not summary_path:
        return
    try:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(f"## Terraform Plan Results\n\n{body}\n")
    except OSError as error:
        raise CommenterError(
            f"Could not write the GitHub step summary: {error}"
        ) from error


def run_commenter(
    options: CommenterOptions, api: Optional[CommentApi]
) -> Optional[str]:
    plans: List[PlanWithChanges] = load_plans(
        options.json_paths, options.log_changed_resources
    )
    body = render_comment(
        plans,
        options.header,
        options.footer,
        options.workflow_link,
    )
    plan_paths = tuple(path for path, _ in plans)
    marker = comment_marker(
        options.repository, options.header, plan_paths, options.workspace
    )
    body = f"{body.rstrip()}\n\n{marker}\n"

    if options.include_plan_job_summary:
        append_job_summary(body, options.step_summary_path)

    if options.pull_request is None:
        print("No pull request context; skipping PR comment.")
        return None
    if not options.repository or "/" not in options.repository:
        raise CommenterError("GITHUB_REPOSITORY is missing or invalid")
    if api is None:
        raise CommenterError("A GitHub API adapter is required to post a PR comment")

    return publish_comment(
        api,
        options.repository,
        options.pull_request,
        body,
        CommentPolicy(
            marker=marker,
            legacy_marker=legacy_comment_marker(options.repository, options.header),
            header=options.header,
            plan_paths=plan_paths,
            replace_existing=options.replace_existing_comments,
            hide_previous=options.hide_previous_comments,
        ),
    )
