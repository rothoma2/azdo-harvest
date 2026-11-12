"""Authentication providers for Azure DevOps REST API requests."""

import base64
import json
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional


AZURE_DEVOPS_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"
HeadersProvider = Callable[[], dict[str, str]]


class AzureDevOpsAuth:
    """Create authentication headers for Azure DevOps API requests.

    PAT authentication is static. Azure CLI authentication obtains an
    Entra access token using the user's existing ``az login`` session and
    refreshes it when it expires.
    """

    def __init__(
        self,
        personal_access_token: Optional[str] = None,
        use_azure_cli: bool = False,
        az_command: str = "az",
    ):
        if use_azure_cli and personal_access_token:
            raise ValueError(
                "Choose either a personal access token or Azure CLI authentication"
            )
        if not use_azure_cli and not personal_access_token:
            raise ValueError(
                "A personal access token is required unless Azure CLI authentication is enabled"
            )

        self._pat = personal_access_token
        self._use_azure_cli = use_azure_cli
        self._az_command = az_command
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = threading.Lock()

    def headers(self) -> dict[str, str]:
        """Return current authentication and content headers."""
        if self._use_azure_cli:
            token = self._get_cli_token()
            authorization = f"Bearer {token}"
        else:
            auth_string = f":{self._pat}"
            b64_auth = base64.b64encode(auth_string.encode()).decode()
            authorization = f"Basic {b64_auth}"

        return {
            "Authorization": authorization,
            "Content-Type": "application/json",
        }

    def _get_cli_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._token and self._expires_at and now < self._expires_at:
            return self._token

        with self._lock:
            now = datetime.now(timezone.utc)
            if self._token and self._expires_at and now < self._expires_at:
                return self._token

            try:
                result = subprocess.run(
                    [
                        self._az_command,
                        "account",
                        "get-access-token",
                        "--resource",
                        AZURE_DEVOPS_RESOURCE_ID,
                        "--output",
                        "json",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "Azure CLI was not found. Install it and run 'az login', "
                    "or use PAT authentication."
                ) from exc
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or "").strip()
                raise RuntimeError(
                    "Azure CLI could not obtain an Azure DevOps access token. "
                    "Run 'az login' and try again"
                    + (f": {detail}" if detail else ".")
                ) from exc

            try:
                payload = json.loads(result.stdout)
                token = payload["accessToken"]
                expires_at = datetime.fromisoformat(
                    payload["expiresOn"].replace("Z", "+00:00")
                )
                if expires_at.tzinfo is None:
                    # Some Azure CLI versions return a UTC value without a
                    # timezone suffix (for example, with a space separator).
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                else:
                    expires_at = expires_at.astimezone(timezone.utc)
            except (ValueError, KeyError, TypeError) as exc:
                raise RuntimeError(
                    "Azure CLI returned an invalid access-token response"
                ) from exc

            # Refresh one minute before expiry to avoid requests crossing the
            # expiry boundary during a search or download.
            self._token = token
            self._expires_at = expires_at - timedelta(minutes=1)
            return token
