import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Set

from commenter_types import Comment, CommenterError


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


class GitHubApi:
    def __init__(
        self,
        token: str,
        api_url: Optional[str] = None,
        graphql_url: Optional[str] = None,
    ) -> None:
        if not token:
            raise CommenterError("A GitHub token is required to post PR comments")
        self.token = token
        self.api_url = (api_url or "https://api.github.com").rstrip("/")
        self.graphql_url = graphql_url or f"{self.api_url}/graphql"

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> "GitHubApi":
        return cls(
            environ.get("INPUT_GITHUB_TOKEN", ""),
            api_url=environ.get("GITHUB_API_URL", ""),
            graphql_url=environ.get("GITHUB_GRAPHQL_URL", ""),
        )

    def request(
        self,
        url: str,
        method: str = "GET",
        payload: Any = None,
    ) -> Any:
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
            raise CommenterError(
                f"GitHub API request failed: {error.reason}"
            ) from error

        if not response_body:
            return {}
        try:
            return json.loads(response_body)
        except json.JSONDecodeError as error:
            raise CommenterError(
                f"GitHub API returned invalid JSON for {url}"
            ) from error

    def list_issue_comments(
        self, repository: str, pull_request: int
    ) -> List[Comment]:
        comments: List[Comment] = []
        page = 1
        while True:
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            url = (
                f"{self.api_url}/repos/{repository}/issues/{pull_request}/comments?"
                f"{query}"
            )
            page_comments = self.request(url)
            if not isinstance(page_comments, list):
                raise CommenterError(
                    "GitHub returned an invalid issue comments response"
                )
            if not all(isinstance(comment, dict) for comment in page_comments):
                raise CommenterError(
                    "GitHub returned an invalid issue comment in the response"
                )
            comments.extend(page_comments)
            if len(page_comments) < 100:
                return comments
            page += 1

    def create_comment(
        self, repository: str, pull_request: int, body: str
    ) -> Comment:
        url = f"{self.api_url}/repos/{repository}/issues/{pull_request}/comments"
        response = self.request(url, method="POST", payload={"body": body})
        if not isinstance(response, dict):
            raise CommenterError("GitHub returned an invalid created-comment response")
        return response

    def update_comment(
        self, repository: str, comment_id: int, body: str
    ) -> Comment:
        url = f"{self.api_url}/repos/{repository}/issues/comments/{comment_id}"
        response = self.request(url, method="PATCH", payload={"body": body})
        if not isinstance(response, dict):
            raise CommenterError("GitHub returned an invalid updated-comment response")
        return response

    def graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        response = self.request(
            self.graphql_url,
            method="POST",
            payload={"query": query, "variables": variables},
        )
        if not isinstance(response, dict):
            raise CommenterError("GitHub returned an invalid GraphQL response")
        errors = response.get("errors")
        if errors:
            messages = "; ".join(
                error.get("message", str(error)) for error in errors
            )
            raise CommenterError(f"GitHub GraphQL request failed: {messages}")
        data = response.get("data") or {}
        if not isinstance(data, dict):
            raise CommenterError("GitHub returned invalid GraphQL data")
        return data

    def minimized_comment_ids(
        self, repository: str, pull_request: int
    ) -> Set[int]:
        owner, name = repository.split("/", 1)
        after = None
        minimized: Set[int] = set()
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
                comment_id = comment.get("databaseId")
                if comment.get("isMinimized") and isinstance(comment_id, int):
                    minimized.add(comment_id)
            page_info = connection["pageInfo"]
            if not page_info["hasNextPage"]:
                return minimized
            after = page_info["endCursor"]

    def minimize_comments(
        self,
        repository: str,
        pull_request: int,
        comments: List[Comment],
    ) -> None:
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
