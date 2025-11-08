"""Data models for Azure DevOps Harvester."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileResult:
    """Represents a file found in Azure DevOps search results.

    Contains all information needed to download the file using Git Items API:
    GET https://dev.azure.com/{organization}/{project}/_apis/git/
    repositories/{repositoryId}/items
    """
    repository: str
    repository_id: Optional[str]
    project: str
    project_id: str
    filepath: str
    branch: str
    commit_id: Optional[str]
    organization: str
    filename: str

    def get_download_url(self, api_version: str = "7.1") -> str:
        """Generate the Azure DevOps API URL to download this file.

        Args:
            api_version: API version to use (default: 7.1)

        Returns:
            Complete URL for the Git Items API
        """

        repo_identifier = self.repository_id or self.repository

        url = (
            f"https://dev.azure.com/{self.organization}/{self.project}/"
            f"_apis/git/repositories/{repo_identifier}/items"
            f"?path={self.filepath}"
            f"&versionDescriptor.version={self.branch}"
            f"&includeContent=true"
            f"&api-version={api_version}"
        )
        return url

    def get_download_params(self) -> dict:
        """Get parameters for downloading this file.

        Returns:
            Dictionary with download parameters for the API
        """
        return {
            "path": self.filepath,
            "versionDescriptor.version": self.branch,
            "includeContent": "true",
            "api-version": "7.1"
        }

    def __str__(self) -> str:
        """String representation of the file result."""
        return f"{self.repository}:{self.filepath} (branch: {self.branch})"


@dataclass
class RepositoryResult:
    """Represents a repository found in Azure DevOps search results."""
    name: str
    project: str
    url: str
    repository_id: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the repository result."""
        return f"{self.project}/{self.name}"
