"""Unit tests for the Terraform PR commenter."""

import json
import os
import tempfile
import unittest
from dataclasses import replace
from typing import List
from unittest.mock import patch

from commenter import (
    comment_marker,
    is_action_comment,
    legacy_comment_marker,
    options_from_environment,
    run_commenter,
)
from commenter_types import Comment, CommenterError, CommenterOptions, CommentPolicy
from plan import (
    classify_resources,
    render_comment,
)


class FakeGitHubApi:
    def __init__(self, comments: List[Comment]) -> None:
        self.comments = comments
        self.created: List[Comment] = []
        self.updated: List[Comment] = []
        self.minimized: List[int] = []

    def list_issue_comments(
        self, repository: str, pull_request: int
    ) -> List[Comment]:
        return self.comments

    def create_comment(
        self, repository: str, pull_request: int, body: str
    ) -> Comment:
        comment = {"id": len(self.created) + 1, "body": body}
        self.created.append(comment)
        return comment

    def update_comment(
        self, repository: str, comment_id: int, body: str
    ) -> Comment:
        comment = {"id": comment_id, "body": body}
        self.updated.append(comment)
        return comment

    def minimize_comments(
        self,
        repository: str,
        pull_request: int,
        comments: List[Comment],
    ) -> None:
        self.minimized.extend(int(comment["id"]) for comment in comments)


class CommentPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.header = "Terraform Plan Changes"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plan_path = os.path.join(self.temp_dir.name, "plan.json")
        with open(self.plan_path, "w", encoding="utf-8") as plan_file:
            json.dump(
                {
                    "resource_changes": [
                        {
                            "address": "aws_instance.web",
                            "change": {"actions": ["create"]},
                        }
                    ]
                },
                plan_file,
            )
        self.marker = comment_marker(
            "example/repo",
            self.header,
            (self.plan_path,),
            workspace=self.temp_dir.name,
        )
        self.options = CommenterOptions(
            json_paths=(self.plan_path,),
            header=self.header,
            footer="",
            include_plan_job_summary=False,
            log_changed_resources=False,
            replace_existing_comments=False,
            hide_previous_comments=True,
            repository="example/repo",
            pull_request=42,
            workflow_link="",
            step_summary_path=None,
            workspace=self.temp_dir.name,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_classifies_replacements_and_ignores_data_source_reads(self) -> None:
        groups = classify_resources(
            {
                "resource_changes": [
                    {"address": "aws_instance.new", "change": {"actions": ["create"]}},
                    {"address": "aws_instance.old", "change": {"actions": ["delete"]}},
                    {"address": "aws_instance.changed", "change": {"actions": ["update"]}},
                    {
                        "address": "aws_instance.replaced",
                        "change": {"actions": ["create", "delete"]},
                    },
                    {"address": "aws_instance.same", "change": {"actions": ["no-op"]}},
                    {"address": "data.aws_ami.image", "change": {"actions": ["read"]}},
                ]
            }
        )
        self.assertEqual(groups.create, ("aws_instance.new",))
        self.assertEqual(groups.delete, ("aws_instance.old",))
        self.assertEqual(groups.update, ("aws_instance.changed",))
        self.assertEqual(groups.replace, ("aws_instance.replaced",))
        self.assertEqual(groups.unchanged, ("aws_instance.same",))

    def test_comment_contains_summary_details_footer_and_workflow_link(self) -> None:
        groups = classify_resources(
            {
                "resource_changes": [
                    {"address": "aws_instance.web", "change": {"actions": ["create"]}}
                ]
            }
        )
        body = render_comment(
            [("terraform.tfplan.json", groups)],
            self.header,
            "Review this plan",
            "[Workflow: Terraform](https://github.com/example/repo/actions/runs/1)",
        )
        self.assertIn(self.header, body)
        self.assertIn("1 to be created", body)
        self.assertIn("+ aws_instance.web", body)
        self.assertIn("Review this plan", body)
        self.assertIn("[Workflow: Terraform]", body)
        self.assertNotIn("Unchanged resources", body)

    def test_comment_limit_includes_marker(self) -> None:
        groups = classify_resources(
            {
                "resource_changes": [
                    {"address": "aws_instance.web", "change": {"actions": ["create"]}}
                ]
            }
        )
        plans = [("terraform.tfplan.json", groups)]
        marker = "<!-- test-marker -->"
        body_without_marker = render_comment(plans, self.header, "", "")
        expected_body = f"{body_without_marker.rstrip()}\n\n{marker}\n"

        with patch("plan.MAX_COMMENT_LENGTH", len(expected_body)):
            body = render_comment(plans, self.header, "", "", marker)

        self.assertEqual(body, expected_body)

    def test_comment_limit_includes_marker_after_compacting(self) -> None:
        resource_address = "aws_instance." + ("x" * 2000)
        groups = classify_resources(
            {
                "resource_changes": [
                    {"address": resource_address, "change": {"actions": ["create"]}}
                ]
            }
        )
        marker = "<!-- test-marker -->"

        with patch("plan.MAX_COMMENT_LENGTH", 512):
            body = render_comment(
                [("terraform.tfplan.json", groups)],
                self.header,
                "",
                "",
                marker,
            )

        self.assertLessEqual(len(body), 512)
        self.assertIn("Resource details were omitted", body)
        self.assertTrue(body.endswith(f"{marker}\n"))

        with patch("plan.MAX_COMMENT_LENGTH", 200):
            with self.assertRaises(CommenterError):
                render_comment(
                    [("terraform.tfplan.json", groups)],
                    self.header,
                    "",
                    "",
                    marker,
                )

    def test_matches_legacy_comments_by_header_and_plan_path(self) -> None:
        plan_path = "terraform.tfplan.json"
        policy = CommentPolicy(
            marker="current-marker",
            legacy_marker=legacy_comment_marker("example/repo", self.header),
            header=self.header,
            plan_paths=(plan_path,),
            replace_existing=True,
            hide_previous=True,
        )
        legacy = {
            "user": {"login": "github-actions"},
            "body": (
                f"{self.header} for `{plan_path}`\n"
                "<b>Terraform Plan: 1 to be created.</b>"
            ),
        }
        self.assertTrue(is_action_comment(legacy, policy))
        legacy["user"] = {"login": "contributor"}
        self.assertFalse(is_action_comment(legacy, policy))
        legacy["body"] += f"\n{policy.legacy_marker}"
        self.assertTrue(is_action_comment(legacy, policy))
        legacy["body"] = legacy["body"].replace(plan_path, "other/plan.json")
        self.assertFalse(is_action_comment(legacy, policy))

    def test_markers_are_unique_to_plan_paths(self) -> None:
        other_marker = comment_marker(
            "example/repo",
            self.header,
            ("module-b/terraform.tfplan.json",),
            workspace=self.temp_dir.name,
        )
        same_path_new_root_marker = comment_marker(
            "example/repo",
            self.header,
            (os.path.join("/new/workspace", "plan.json"),),
            workspace="/new/workspace",
        )
        self.assertNotEqual(self.marker, other_marker)
        self.assertEqual(self.marker, same_path_new_root_marker)

    def test_environment_options_capture_event_and_comment_policy(self) -> None:
        event_path = os.path.join(self.temp_dir.name, "event.json")
        with open(event_path, "w", encoding="utf-8") as event_file:
            json.dump({"pull_request": {"number": 42}}, event_file)

        options = options_from_environment(
            {
                "INPUT_JSON_FILES": self.plan_path,
                "INPUT_INCLUDE_WORKFLOW_LINK": "false",
                "INPUT_INCLUDE_PLAN_JOB_SUMMARY": "false",
                "INPUT_REPLACE_EXISTING_COMMENTS": "true",
                "INPUT_HIDE_PREVIOUS_COMMENTS": "false",
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_EVENT_PATH": event_path,
                "GITHUB_REPOSITORY": "example/repo",
            }
        )

        self.assertEqual(options.pull_request, 42)
        self.assertEqual(options.repository, "example/repo")
        self.assertTrue(options.replace_existing_comments)
        self.assertFalse(options.hide_previous_comments)
        self.assertFalse(options.include_plan_job_summary)
        self.assertEqual(options.workflow_link, "")

    def test_replace_mode_updates_the_latest_matching_comment(self) -> None:
        comments = [
            {
                "id": 10,
                "updated_at": "2026-01-01T00:00:00Z",
                "body": self.marker,
            },
            {
                "id": 11,
                "updated_at": "2026-02-01T00:00:00Z",
                "body": self.marker,
            },
        ]
        api = FakeGitHubApi(comments)
        options = replace(self.options, replace_existing_comments=True)
        result = run_commenter(options, api)
        self.assertEqual(result, "updated")
        self.assertEqual(api.updated[0]["id"], 11)
        self.assertIn("aws_instance.web", api.updated[0]["body"])
        self.assertEqual(api.minimized, [10])
        self.assertEqual(api.created, [])

    def test_replace_mode_creates_first_comment_when_no_match_exists(self) -> None:
        api = FakeGitHubApi([])
        options = replace(self.options, replace_existing_comments=True)
        result = run_commenter(options, api)
        self.assertEqual(result, "created")
        self.assertIn("aws_instance.web", api.created[0]["body"])
        self.assertEqual(api.updated, [])

    def test_replace_mode_does_not_update_a_different_plan_path(self) -> None:
        other_path = "module-b/terraform.tfplan.json"
        other_marker = comment_marker(
            "example/repo",
            self.header,
            (other_path,),
            workspace=self.temp_dir.name,
        )
        api = FakeGitHubApi(
            [
                {
                    "id": 10,
                    "updated_at": "2026-02-01T00:00:00Z",
                    "user": {"login": "github-actions"},
                    "body": (
                        f"{self.header} for `{other_path}`\n"
                        f"{other_marker}\n"
                        "<b>Terraform Plan: 1 to be created.</b>"
                    ),
                }
            ]
        )
        options = replace(self.options, replace_existing_comments=True)

        result = run_commenter(options, api)

        self.assertEqual(result, "created")
        self.assertEqual(api.updated, [])
        self.assertEqual(api.minimized, [])
        self.assertEqual(len(api.created), 1)

    def test_default_mode_hides_previous_comment_then_creates(self) -> None:
        api = FakeGitHubApi([{"id": 10, "body": self.marker}])
        result = run_commenter(self.options, api)
        self.assertEqual(result, "created")
        self.assertEqual(api.minimized, [10])
        self.assertIn("Terraform Plan: 1 to be created", api.created[0]["body"])
        self.assertEqual(api.updated, [])


if __name__ == "__main__":
    unittest.main()
