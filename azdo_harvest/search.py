"""Azure DevOps search functionality using the REST API."""
import base64
import requests
from typing import Optional, Dict, List, Any
from azdo_harvest.models import FileResult
from azdo_harvest.downloader import FileDownloader


class AzureDevOpsSearcher:
    """Client for searching Azure DevOps repositories and files."""

    def __init__(self, organization: str, project: str,
                 personal_access_token: str):
        """Initialize the Azure DevOps searcher.

        Args:
            organization: Azure DevOps organization name
            personal_access_token: Personal Access Token for authentication
        """

        self.organization = organization
        self.base_url = f"https://dev.azure.com/{organization}"
        self.search_url = f"https://almsearch.dev.azure.com/{organization}"

        auth_string = f":{personal_access_token}"
        b64_auth = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json"
        }
        self.downloader = FileDownloader(self.headers)

    def search(
        self,
        search_term: str,
        project: Optional[str] = None,
        search_files: bool = True,
        search_repos: bool = True,
        max_results: int = 100
    ) -> Dict[str, List]:
        """Search for repositories and files in Azure DevOps.

        Args:
            search_term: The term to search for
            project: Optional project to limit search scope
            search_files: Whether to search in file contents
            search_repos: Whether to search repository names
            max_results: Maximum number of results per search type

        Returns:
            Dictionary with 'repositories' (list of dicts) and
            'files' (list of FileResult objects) keys
        """
        results = {
            'repositories': [],
            'files': []
        }

        if search_repos:
            results['repositories'] = self._search_repositories(
                search_term, project, max_results
            )

        if search_files:
            results['files'] = self._search_code(
                search_term, project, max_results
            )

        return results

    def _search_repositories(
        self,
        search_term: str,
        project: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for repositories by name.

        Args:
            search_term: The term to search for
            project: Optional project to limit search scope
            max_results: Maximum number of results

        Returns:
            List of repository information
        """
        url = f"{self.search_url}/_apis/search/codesearchresults"
        params = {"api-version": "7.1-preview.1"}

        payload = {
            "searchText": search_term,
            "$top": max_results,
            "$skip": 0
        }

        if project:
            payload["filters"] = {
                "Project": [project]
            }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            repositories = []
            for result in data.get('results', []):
                repo_info = {
                    'name': result.get('repository', {}).get('name', 'N/A'),
                    'project': result.get('project', {}).get('name', 'N/A'),
                    'url': result.get('repository', {}).get(
                        'remoteUrl', 'N/A'
                    )
                }
                repositories.append(repo_info)

            return repositories

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search repositories: {str(e)}")

    def _search_code(
        self,
        search_term: str,
        project: Optional[str] = None,
        max_results: int = 100
    ) -> List[FileResult]:
        """Search for code in files.

        Args:
            search_term: The term to search for
            project: Optional project to limit search scope
            max_results: Maximum number of results

        Returns:
            List of FileResult objects with download information
        """
        url = f"{self.search_url}/_apis/search/codesearchresults"
        params = {"api-version": "7.1-preview.1"}

        payload = {
            "searchText": search_term,
            "$top": max_results,
            "$skip": 0
        }

        if project:
            payload["filters"] = {
                "Project": [project]
            }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            files = []
            for result in data.get('results', []):
                # Extract version information
                versions = result.get('versions', [])
                if versions:
                    branch = versions[0].get('branchName', 'main')
                    commit_id = versions[0].get('changeId')
                else:
                    branch = 'main'
                    commit_id = None

                # Create FileResult object
                file_result = FileResult(
                    repository=result.get('repository', {}).get(
                        'name', 'N/A'
                    ),
                    repository_id=result.get('repository', {}).get('id'),
                    project=result.get('project', {}).get('name', 'N/A'),
                    project_id=result.get('project', {}).get(
                        'id', '00000000-0000-0000-0000-000000000000'
                    ),
                    filepath=result.get('path', 'N/A'),
                    branch=branch,
                    commit_id=commit_id,
                    organization=self.organization,
                    filename=result.get('fileName', 'N/A')
                )
                files.append(file_result)

            return files

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search code: {str(e)}")
