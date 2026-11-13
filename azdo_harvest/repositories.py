"""Utilities for listing Azure DevOps Git repositories."""

from typing import Any, Optional
from urllib.parse import quote

import requests

from azdo_harvest.auth import AzureDevOpsAuth


def list_repositories(
    organization: str,
    project: Optional[str] = None,
    auth: Optional[AzureDevOpsAuth] = None,
) -> list[dict[str, Any]]:
    """Return Git repositories visible to the authenticated user."""
    auth = auth or AzureDevOpsAuth(use_azure_cli=True)
    project_path = f"/{quote(project, safe='')}" if project else ""
    url = (
        f"https://dev.azure.com/{quote(organization, safe='')}"
        f"{project_path}/_apis/git/repositories"
    )
    params = {"api-version": "7.1", "includeHidden": "false"}
    repositories: list[dict[str, Any]] = []
    continuation_token: Optional[str] = None

    while True:
        request_params = dict(params)
        if continuation_token:
            request_params["continuationToken"] = continuation_token
        response = requests.get(
            url, headers=auth.headers(), params=request_params, timeout=30
        )
        response.raise_for_status()
        repositories.extend(response.json().get("value", []))

        # Some Azure DevOps deployments paginate this endpoint with a header.
        next_token = response.headers.get("x-ms-continuationtoken")
        if not next_token or next_token == continuation_token:
            break
        continuation_token = next_token

    return repositories


def write_repository_names(
    repositories: list[dict[str, Any]], output_file: str
) -> None:
    """Write one repository name per line to ``output_file``."""
    with open(output_file, "w", encoding="utf-8") as handle:
        for repository in repositories:
            handle.write(f"{repository.get('name', '')}\n")
