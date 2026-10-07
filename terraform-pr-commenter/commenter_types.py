from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple


Comment = Dict[str, Any]


class CommenterError(Exception):
    """An expected input, plan, or GitHub API failure safe to report to Actions."""


@dataclass(frozen=True)
class ResourceChanges:
    create: Tuple[str, ...] = ()
    delete: Tuple[str, ...] = ()
    update: Tuple[str, ...] = ()
    replace: Tuple[str, ...] = ()
    unchanged: Tuple[str, ...] = ()

    @property
    def has_resources(self) -> bool:
        return any(
            (
                self.create,
                self.delete,
                self.update,
                self.replace,
                self.unchanged,
            )
        )

    def changed_resources(self) -> Dict[str, Tuple[str, ...]]:
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
    workspace: Optional[str]


@dataclass(frozen=True)
class CommentPolicy:
    marker: str
    legacy_marker: str
    header: str
    plan_paths: Tuple[str, ...]
    replace_existing: bool
    hide_previous: bool


class CommentApi(Protocol):
    """Port used by the comment workflow; GitHub and test adapters implement it."""

    def list_issue_comments(
        self, repository: str, pull_request: int
    ) -> List[Comment]:
        ...

    def create_comment(
        self, repository: str, pull_request: int, body: str
    ) -> Comment:
        ...

    def update_comment(self, repository: str, comment_id: int, body: str) -> Comment:
        ...

    def minimize_comments(
        self, repository: str, pull_request: int, comments: List[Comment]
    ) -> None:
        ...
