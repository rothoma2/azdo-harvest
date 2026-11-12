"""Tests for Azure DevOps authentication providers."""

import base64
import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from azdo_harvest.auth import AzureDevOpsAuth, AZURE_DEVOPS_RESOURCE_ID


def test_pat_headers_use_basic_auth():
    headers = AzureDevOpsAuth(personal_access_token="secret").headers()

    assert headers["Authorization"] == (
        "Basic " + base64.b64encode(b":secret").decode()
    )


@patch("azdo_harvest.auth.subprocess.run")
def test_azure_cli_headers_use_bearer_token_and_cache(mock_run):
    mock_run.return_value = Mock(
        stdout=json.dumps({
            "accessToken": "short-lived-token",
            "expiresOn": "2099-01-01T00:00:00Z",
        })
    )
    auth = AzureDevOpsAuth(use_azure_cli=True)

    assert auth.headers()["Authorization"] == "Bearer short-lived-token"
    assert auth.headers()["Authorization"] == "Bearer short-lived-token"
    mock_run.assert_called_once_with(
        [
            "az", "account", "get-access-token", "--resource",
            AZURE_DEVOPS_RESOURCE_ID, "--output", "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_auth_requires_one_method():
    with pytest.raises(ValueError):
        AzureDevOpsAuth()

    with pytest.raises(ValueError):
        AzureDevOpsAuth(personal_access_token="pat", use_azure_cli=True)


@patch("azdo_harvest.auth.subprocess.run")
def test_azure_cli_errors_are_actionable(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "az", stderr="Please run az login"
    )

    with pytest.raises(RuntimeError, match="az login"):
        AzureDevOpsAuth(use_azure_cli=True).headers()
