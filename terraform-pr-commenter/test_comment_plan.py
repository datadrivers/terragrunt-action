import json
import os
import tempfile
import unittest
from dataclasses import replace

from comment_plan import (
    CommenterOptions,
    classify_resources,
    comment_marker,
    is_action_comment,
    render_comment,
    run_commenter,
)


class FakeGitHubApi:
    def __init__(self, comments):
        self.comments = comments
        self.created = []
        self.updated = []
        self.minimized = []

    def list_issue_comments(self, repository, pull_request):
        return self.comments

    def create_comment(self, repository, pull_request, body):
        self.created.append(body)

    def update_comment(self, repository, comment_id, body):
        self.updated.append((comment_id, body))

    def minimize_comments(self, repository, pull_request, comments):
        self.minimized.extend(comment["id"] for comment in comments)


class CommentPlanTests(unittest.TestCase):
    def setUp(self):
        self.header = "Terraform Plan Changes"
        self.marker = comment_marker("example/repo", self.header)
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
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_classifies_replacements_and_ignores_data_source_reads(self):
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

    def test_comment_contains_summary_details_footer_and_workflow_link(self):
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

    def test_matches_legacy_comments_only_for_github_actions_bot(self):
        legacy = {
            "user": {"login": "github-actions[bot]"},
            "body": (
                f"{self.header} for `terraform.tfplan.json`\n"
                "<b>Terraform Plan: 1 to be created.</b>"
            ),
        }
        self.assertTrue(is_action_comment(legacy, self.marker, self.header))
        legacy["user"] = {"login": "contributor"}
        self.assertFalse(is_action_comment(legacy, self.marker, self.header))

    def test_replace_mode_updates_the_latest_matching_comment(self):
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
        self.assertEqual(api.updated[0][0], 11)
        self.assertIn("aws_instance.web", api.updated[0][1])
        self.assertEqual(api.minimized, [10])
        self.assertEqual(api.created, [])

    def test_replace_mode_creates_first_comment_when_no_match_exists(self):
        api = FakeGitHubApi([])
        options = replace(self.options, replace_existing_comments=True)
        result = run_commenter(options, api)
        self.assertEqual(result, "created")
        self.assertIn("aws_instance.web", api.created[0])
        self.assertEqual(api.updated, [])

    def test_default_mode_hides_previous_comment_then_creates(self):
        api = FakeGitHubApi([{"id": 10, "body": self.marker}])
        result = run_commenter(self.options, api)
        self.assertEqual(result, "created")
        self.assertEqual(api.minimized, [10])
        self.assertIn("Terraform Plan: 1 to be created", api.created[0])
        self.assertEqual(api.updated, [])


if __name__ == "__main__":
    unittest.main()
