#!/usr/bin/env python3

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional, Protocol, Tuple


MAX_COMMENT_LENGTH = 65536
GRAPHQL_COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      comments(first: 100, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
        nodes {
          databaseId
          isMinimized
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""
MINIMIZE_COMMENT_MUTATION = """
mutation($id: ID!) {
  minimizeComment(input: {classifier: OUTDATED, subjectId: $id}) {
    clientMutationId
  }
}
"""


class CommenterError(Exception):
    pass


@dataclass(frozen=True)
class ResourceChanges:
    create: Tuple[str, ...] = ()
    delete: Tuple[str, ...] = ()
    update: Tuple[str, ...] = ()
    replace: Tuple[str, ...] = ()
    unchanged: Tuple[str, ...] = ()

    @property
    def has_resources(self):
        return any(
            (
                self.create,
                self.delete,
                self.update,
                self.replace,
                self.unchanged,
            )
        )

    def changed_resources(self):
        return {
            name: resources
            for name, resources in (
                ("create", self.create),
                ("delete", self.delete),
                ("update", self.update),
                ("replace", self.replace),
            )
            if resources
        }


@dataclass(frozen=True)
class CommenterOptions:
    json_paths: Tuple[str, ...]
    header: str
    footer: str
    include_plan_job_summary: bool
    log_changed_resources: bool
    replace_existing_comments: bool
    hide_previous_comments: bool
    repository: str
    pull_request: Optional[int]
    workflow_link: str
    step_summary_path: Optional[str]


@dataclass(frozen=True)
class CommentPolicy:
    marker: str
    header: str
    replace_existing: bool
    hide_previous: bool


class CommentApi(Protocol):
    def list_issue_comments(self, repository, pull_request):
        ...

    def create_comment(self, repository, pull_request, body):
        ...

    def update_comment(self, repository, comment_id, body):
        ...

    def minimize_comments(self, repository, pull_request, comments):
        ...


def input_bool(name, default, environ):
    value = environ.get(name)
    if value is None or value == "":
        return default
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise CommenterError(f"{name} must be 'true' or 'false', got {value!r}")


def classify_resources(plan):
    groups = {name: [] for name in ("create", "delete", "update", "replace", "unchanged")}
    resource_changes = plan.get("resource_changes") or []
    if not isinstance(resource_changes, list):
        raise CommenterError("Plan JSON field 'resource_changes' must be an array")

    for resource in resource_changes:
        change = resource.get("change") or {}
        actions = change.get("actions") or []
        address = resource.get("address", "(unknown resource)")
        if "create" in actions and "delete" in actions:
            groups["replace"].append(address)
        elif actions == ["create"]:
            groups["create"].append(address)
        elif actions == ["delete"]:
            groups["delete"].append(address)
        elif actions == ["update"]:
            groups["update"].append(address)
        elif actions == ["no-op"]:
            groups["unchanged"].append(address)
    return ResourceChanges(
        **{name: tuple(resources) for name, resources in groups.items()}
    )


def resource_details(title, resources, operator, replacement=False):
    if not resources:
        return ""
    lines = [f"#### {title}", "", "```diff"]
    for resource in resources:
        if replacement:
            lines.append(f"- {resource}")
        lines.append(f"{operator} {resource}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_plan(path, groups, header, footer, workflow_link, include_details=True):
    create = len(groups.create)
    delete = len(groups.delete)
    update = len(groups.update)
    replace = len(groups.replace)
    unchanged = len(groups.unchanged)
    summary = (
        f"<b>Terraform Plan: {create} to be created, {delete} to be deleted, "
        f"{update} to be updated, {replace} to be replaced, "
        f"{unchanged} unchanged.</b>"
    )
    parts = [f"{header} for `{path}`", "<details>", "<summary>", summary, "</summary>", ""]

    if not groups.has_resources:
        parts.extend(["<p>There were no changes done to the infrastructure.</p>", ""])
    elif include_details:
        parts.extend(
            [
                resource_details("Resources to create", groups.create, "+"),
                resource_details("Resources to delete", groups.delete, "-"),
                resource_details("Resources to update", groups.update, "!"),
                resource_details("Resources to replace", groups.replace, "+", replacement=True),
            ]
        )
    parts.extend(["</details>", ""])
    if footer:
        parts.extend([footer, ""])
    if workflow_link:
        parts.extend([workflow_link, ""])
    return "\n".join(part for part in parts if part is not None)


def render_comment(plans, header, footer, workflow_link):
    full = "\n".join(
        render_plan(path, groups, header, footer, workflow_link)
        for path, groups in plans
    )
    if len(full) <= MAX_COMMENT_LENGTH:
        return full

    compact = "\n".join(
        render_plan(path, groups, header, footer, workflow_link, include_details=False)
        for path, groups in plans
    )
    if len(compact) > MAX_COMMENT_LENGTH:
        raise CommenterError(
            "The generated PR comment exceeds GitHub's comment size limit, "
            "even after omitting resource details"
        )
    return (
        compact
        + "\n<p>Resource details were omitted because the full plan exceeded "
        + f"GitHub's comment size limit ({MAX_COMMENT_LENGTH} characters). "
        + "See the workflow run for the complete plan.</p>\n"
    )


def comment_marker(repository, header):
    value = f"{repository.lower()}\0{header}".encode("utf-8")
    digest = hashlib.sha256(value).hexdigest()[:20]
    return f"<!-- terragrunt-action-pr-commenter:v1:{digest} -->"


def is_action_comment(comment, marker, header):
    body = comment.get("body") or ""
    if marker in body:
        return True

    user = comment.get("user") or {}
    if user.get("login") != "github-actions[bot]":
        return False
    return (
        body.lstrip().startswith(f"{header} for `")
        and "<b>Terraform Plan:" in body
    )


def select_latest_comment(comments):
    return max(
        comments,
        key=lambda comment: comment.get("updated_at")
        or comment.get("created_at")
        or "",
    )


class GitHubApi:
    def __init__(self, token, api_url=None, graphql_url=None):
        if not token:
            raise CommenterError("A GitHub token is required to post PR comments")
        self.token = token
        self.api_url = (api_url or "https://api.github.com").rstrip("/")
        self.graphql_url = graphql_url or f"{self.api_url}/graphql"

    @classmethod
    def from_environment(cls, environ):
        return cls(
            environ.get("INPUT_GITHUB_TOKEN", ""),
            api_url=environ.get("GITHUB_API_URL"),
            graphql_url=environ.get("GITHUB_GRAPHQL_URL"),
        )

    def request(self, url, method="GET", payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "terragrunt-action-pr-commenter",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            response_body = error.read()
            try:
                detail = json.loads(response_body).get("message", "")
            except (json.JSONDecodeError, AttributeError):
                detail = response_body.decode("utf-8", errors="replace")
            raise CommenterError(
                f"GitHub API {method} {url} failed with HTTP "
                f"{error.code}: {detail or error.reason}"
            ) from error
        except urllib.error.URLError as error:
            raise CommenterError(f"GitHub API request failed: {error.reason}") from error

        if not response_body:
            return {}
        try:
            return json.loads(response_body)
        except json.JSONDecodeError as error:
            raise CommenterError(f"GitHub API returned invalid JSON for {url}") from error

    def list_issue_comments(self, repository, pull_request):
        comments = []
        page = 1
        while True:
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            url = (
                f"{self.api_url}/repos/{repository}/issues/{pull_request}/comments?"
                f"{query}"
            )
            page_comments = self.request(url)
            if not isinstance(page_comments, list):
                raise CommenterError("GitHub returned an invalid issue comments response")
            comments.extend(page_comments)
            if len(page_comments) < 100:
                return comments
            page += 1

    def create_comment(self, repository, pull_request, body):
        url = f"{self.api_url}/repos/{repository}/issues/{pull_request}/comments"
        return self.request(url, method="POST", payload={"body": body})

    def update_comment(self, repository, comment_id, body):
        url = f"{self.api_url}/repos/{repository}/issues/comments/{comment_id}"
        return self.request(url, method="PATCH", payload={"body": body})

    def graphql(self, query, variables):
        response = self.request(
            self.graphql_url,
            method="POST",
            payload={"query": query, "variables": variables},
        )
        errors = response.get("errors")
        if errors:
            messages = "; ".join(error.get("message", str(error)) for error in errors)
            raise CommenterError(f"GitHub GraphQL request failed: {messages}")
        return response.get("data") or {}

    def minimized_comment_ids(self, repository, pull_request):
        owner, name = repository.split("/", 1)
        after = None
        minimized = set()
        while True:
            data = self.graphql(
                GRAPHQL_COMMENTS_QUERY,
                {"owner": owner, "name": name, "number": pull_request, "after": after},
            )
            pull = (data.get("repository") or {}).get("pullRequest")
            if pull is None:
                raise CommenterError(
                    f"Pull request #{pull_request} was not found in {repository}"
                )
            connection = pull["comments"]
            for comment in connection["nodes"]:
                if comment.get("isMinimized") and comment.get("databaseId") is not None:
                    minimized.add(comment["databaseId"])
            page_info = connection["pageInfo"]
            if not page_info["hasNextPage"]:
                return minimized
            after = page_info["endCursor"]

    def minimize_comments(self, repository, pull_request, comments):
        if not comments:
            return
        minimized = self.minimized_comment_ids(repository, pull_request)
        for comment in comments:
            if comment.get("id") in minimized:
                continue
            node_id = comment.get("node_id")
            if not node_id:
                raise CommenterError(
                    f"Comment {comment.get('id')} is missing its GitHub node ID"
                )
            self.graphql(MINIMIZE_COMMENT_MUTATION, {"id": node_id})


def publish_comment(api, repository, pull_request, body, policy):
    comments = api.list_issue_comments(repository, pull_request)
    matching = [
        comment
        for comment in comments
        if is_action_comment(comment, policy.marker, policy.header)
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


def pull_request_number(event_name, event):
    if event_name not in {"pull_request", "pull_request_target", "workflow_call"}:
        return None
    pull_request = event.get("pull_request") or {}
    number = pull_request.get("number")
    if number is None and event_name == "workflow_call":
        number = event.get("number")
    return number


def options_from_environment(environ=None):
    environ = os.environ if environ is None else environ
    paths = tuple(
        path.strip()
        for path in environ.get("INPUT_JSON_FILES", "").splitlines()
        if path.strip()
    )
    if not paths:
        raise CommenterError("No Terraform plan JSON files were provided")

    event = {}
    event_path = environ.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            with open(event_path, encoding="utf-8") as event_file:
                event = json.load(event_file)
        except OSError as error:
            raise CommenterError(f"Could not read GitHub event payload: {error}") from error
        except json.JSONDecodeError as error:
            raise CommenterError(f"Invalid GitHub event payload: {error}") from error

    event_name = environ.get("GITHUB_EVENT_NAME", "")
    if not isinstance(event, dict):
        raise CommenterError("GitHub event payload must be a JSON object")
    repository = environ.get("GITHUB_REPOSITORY", "")
    workflow_link = ""
    include_workflow_link = input_bool("INPUT_INCLUDE_WORKFLOW_LINK", True, environ)
    if include_workflow_link:
        server_url = environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        run_id = environ.get("GITHUB_RUN_ID", "")
        workflow = environ.get("GITHUB_WORKFLOW", "")
        if repository and run_id:
            workflow_link = (
                f"[Workflow: {workflow}]({server_url}/{repository}/actions/runs/{run_id})"
            )

    return CommenterOptions(
        json_paths=paths,
        header=environ.get("INPUT_COMMENT_HEADER", "Terraform Plan Changes"),
        footer=environ.get("INPUT_COMMENT_FOOTER", ""),
        include_plan_job_summary=input_bool(
            "INPUT_INCLUDE_PLAN_JOB_SUMMARY", True, environ
        ),
        log_changed_resources=input_bool("INPUT_LOG_CHANGED_RESOURCES", True, environ),
        replace_existing_comments=input_bool(
            "INPUT_REPLACE_EXISTING_COMMENTS", False, environ
        ),
        hide_previous_comments=input_bool("INPUT_HIDE_PREVIOUS_COMMENTS", True, environ),
        repository=repository,
        pull_request=pull_request_number(event_name, event),
        workflow_link=workflow_link,
        step_summary_path=environ.get("GITHUB_STEP_SUMMARY"),
    )


def load_plans(paths, log_changed_resources):
    plans = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as plan_file:
                plan = json.load(plan_file)
        except OSError as error:
            raise CommenterError(f"Could not read plan JSON file {path}: {error}") from error
        except json.JSONDecodeError as error:
            raise CommenterError(f"Invalid plan JSON in {path}: {error}") from error
        if not isinstance(plan, dict):
            raise CommenterError(f"Plan JSON in {path} must be an object")
        groups = classify_resources(plan)
        if log_changed_resources:
            print(
                f"Changed resources in {path}: "
                f"{json.dumps(groups.changed_resources())}"
            )
        plans.append((path, groups))
    return plans


def append_job_summary(body, summary_path):
    if not summary_path:
        return
    try:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(f"## Terraform Plan Results\n\n{body}\n")
    except OSError as error:
        raise CommenterError(f"Could not write the GitHub step summary: {error}") from error


def run_commenter(options, api):
    plans = load_plans(options.json_paths, options.log_changed_resources)
    body = render_comment(
        plans,
        options.header,
        options.footer,
        options.workflow_link,
    )
    marker = comment_marker(options.repository, options.header)
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
            header=options.header,
            replace_existing=options.replace_existing_comments,
            hide_previous=options.hide_previous_comments,
        ),
    )


def run():
    options = options_from_environment()
    api = None
    if options.pull_request is not None:
        api = GitHubApi.from_environment(os.environ)
    run_commenter(options, api)


if __name__ == "__main__":
    try:
        run()
    except CommenterError as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
