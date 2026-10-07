import json
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from commenter_types import CommenterError, ResourceChanges


MAX_COMMENT_LENGTH = 65536
PlanWithChanges = Tuple[str, ResourceChanges]


def classify_resources(plan: Mapping[str, Any]) -> ResourceChanges:
    groups: Dict[str, List[str]] = {
        name: []
        for name in ("create", "delete", "update", "replace", "unchanged")
    }
    resource_changes = plan.get("resource_changes") or []
    if not isinstance(resource_changes, list):
        raise CommenterError("Plan JSON field 'resource_changes' must be an array")

    for resource in resource_changes:
        if not isinstance(resource, dict):
            raise CommenterError("Each resource change in a plan must be an object")
        change = resource.get("change") or {}
        if not isinstance(change, dict):
            raise CommenterError("Resource change field 'change' must be an object")
        actions = change.get("actions") or []
        if not isinstance(actions, list):
            raise CommenterError("Resource change field 'actions' must be an array")
        address = resource.get("address", "(unknown resource)")
        if not isinstance(address, str):
            raise CommenterError("Resource change field 'address' must be a string")

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


def resource_details(
    title: str,
    resources: Sequence[str],
    operator: str,
    replacement: bool = False,
) -> str:
    if not resources:
        return ""
    lines = [f"#### {title}", "", "```diff"]
    for resource in resources:
        if replacement:
            lines.append(f"- {resource}")
        lines.append(f"{operator} {resource}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_plan(
    path: str,
    groups: ResourceChanges,
    header: str,
    footer: str,
    workflow_link: str,
    include_details: bool = True,
) -> str:
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
    parts = [
        f"{header} for `{path}`",
        "<details>",
        "<summary>",
        summary,
        "</summary>",
        "",
    ]

    if not groups.has_resources:
        parts.extend(["<p>There were no changes done to the infrastructure.</p>", ""])
    elif include_details:
        parts.extend(
            [
                resource_details("Resources to create", groups.create, "+"),
                resource_details("Resources to delete", groups.delete, "-"),
                resource_details("Resources to update", groups.update, "!"),
                resource_details(
                    "Resources to replace", groups.replace, "+", replacement=True
                ),
            ]
        )
    parts.extend(["</details>", ""])
    if footer:
        parts.extend([footer, ""])
    if workflow_link:
        parts.extend([workflow_link, ""])
    return "\n".join(part for part in parts if part is not None)


def _append_marker(body: str, marker: str) -> str:
    if not marker:
        return body
    return f"{body.rstrip()}\n\n{marker}\n"


def render_comment(
    plans: Sequence[PlanWithChanges],
    header: str,
    footer: str,
    workflow_link: str,
    marker: str = "",
) -> str:
    full = _append_marker(
        "\n".join(
            render_plan(path, groups, header, footer, workflow_link)
            for path, groups in plans
        ),
        marker,
    )
    if len(full) <= MAX_COMMENT_LENGTH:
        return full

    compact = "\n".join(
        render_plan(
            path, groups, header, footer, workflow_link, include_details=False
        )
        for path, groups in plans
    )
    compact = _append_marker(
        compact
        + "\n<p>Resource details were omitted because the full plan exceeded "
        + f"GitHub's comment size limit ({MAX_COMMENT_LENGTH} characters). "
        + "See the workflow run for the complete plan.</p>\n",
        marker,
    )
    if len(compact) > MAX_COMMENT_LENGTH:
        raise CommenterError(
            "The generated PR comment exceeds GitHub's comment size limit, "
            "even after omitting resource details"
        )
    return compact


def load_plans(
    paths: Sequence[str], log_changed_resources: bool
) -> List[PlanWithChanges]:
    plans: List[PlanWithChanges] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as plan_file:
                plan = json.load(plan_file)
        except OSError as error:
            raise CommenterError(
                f"Could not read plan JSON file {path}: {error}"
            ) from error
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
