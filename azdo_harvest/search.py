"""Azure DevOps search functionality using the REST API."""
import requests
from typing import Optional, Dict, List, Any
from azdo_harvest.models import FileResult
from azdo_harvest.downloader import FileDownloader
from azdo_harvest.auth import AzureDevOpsAuth


CODE_SEARCH_PAGE_SIZE = 1000
REPOSITORY_BATCH_SIZE = 500
CODE_SEARCH_TIMEOUT_SECONDS = 120


class AzureDevOpsSearcher:
    """Client for searching Azure DevOps repositories and files."""

    def __init__(self, organization: str, project: str,
                 personal_access_token: Optional[str] = None,
                 use_azure_cli: bool = False,
                 az_command: str = "az"):
        """Initialize the Azure DevOps searcher.

        Args:
            organization: Azure DevOps organization name
            personal_access_token: Personal Access Token for authentication
            use_azure_cli: Obtain a short-lived token using Azure CLI
            az_command: Azure CLI executable to use
        """

        self.organization = organization
        self.base_url = f"https://dev.azure.com/{organization}"
        self.search_url = f"https://almsearch.dev.azure.com/{organization}"

        self.auth = AzureDevOpsAuth(
            personal_access_token=personal_access_token,
            use_azure_cli=use_azure_cli,
            az_command=az_command,
        )
        self.downloader = FileDownloader(self.auth.headers)

    @property
    def headers(self) -> dict[str, str]:
        """Return current authentication headers (kept for compatibility)."""
        return self.auth.headers()

    def search(
        self,
        search_term: str,
        project: Optional[str] = None,
        search_files: bool = True,
        search_repos: bool = True,
        max_results: int = 100,
        repository_names: Optional[List[str]] = None,
    ) -> Dict[str, List]:
        """Search for repositories and files in Azure DevOps.

        Args:
            search_term: The term to search for
            project: Optional project to limit search scope
            search_files: Whether to search in file contents
            search_repos: Whether to search repository names
            max_results: Maximum number of results per search type
            repository_names: Optional repository allowlist, sent in batches
                of 500 names.

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
                search_term, project, max_results, repository_names
            )

        if search_files:
            results['files'] = self._search_code(
                search_term, project, max_results, repository_names
            )

        return results

    def _search_repositories(
        self,
        search_term: str,
        project: Optional[str] = None,
        max_results: int = 1000,
        repository_names: Optional[List[str]] = None,
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

        try:
            repositories = []
            seen = set()
            for batch in self._repository_batches(repository_names):
                remaining = max_results - len(repositories)
                if remaining <= 0:
                    break
                payload = self._search_payload(search_term, project, batch)
                for data in self._search_pages(url, params, payload, remaining):
                    for result in data.get('results', []):
                        repo = result.get('repository', {})
                        project_info = result.get('project', {})
                        repo_info = {
                            'name': repo.get('name', 'N/A'),
                            'project': project_info.get('name', 'N/A'),
                            'url': repo.get('remoteUrl', 'N/A')
                        }
                        key = (
                            project_info.get('id', repo_info['project']),
                            repo.get('id', repo_info['name']),
                            repo_info['url'],
                        )
                        if key not in seen:
                            seen.add(key)
                            repositories.append(repo_info)

            return repositories

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search repositories: {str(e)}")

    def _search_code(
        self,
        search_term: str,
        project: Optional[str] = None,
        max_results: int = 100,
        repository_names: Optional[List[str]] = None,
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

        try:
            files = []
            seen = set()
            for batch in self._repository_batches(repository_names):
                remaining = max_results - len(files)
                if remaining <= 0:
                    break
                payload = self._search_payload(search_term, project, batch)
                for data in self._search_pages(url, params, payload, remaining):
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
                        repository = result.get('repository', {})
                        project_info = result.get('project', {})
                        file_result = FileResult(
                            repository=repository.get('name', 'N/A'),
                            repository_id=repository.get('id'),
                            project=project_info.get('name', 'N/A'),
                            project_id=project_info.get(
                                'id', '00000000-0000-0000-0000-000000000000'
                            ),
                            filepath=result.get('path', 'N/A'),
                            branch=branch,
                            commit_id=commit_id,
                            organization=self.organization,
                            filename=result.get('fileName', 'N/A')
                        )
                        key = (
                            file_result.project_id,
                            file_result.repository_id or file_result.repository,
                            file_result.filepath,
                            file_result.branch,
                        )
                        if key not in seen:
                            seen.add(key)
                            files.append(file_result)

            return files

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to search code: {str(e)}")

    @staticmethod
    def _repository_batches(repository_names: Optional[List[str]]):
        """Yield repository filter batches, or one unfiltered search."""
        if repository_names is None:
            yield None
            return

        for start in range(0, len(repository_names), REPOSITORY_BATCH_SIZE):
            yield repository_names[start:start + REPOSITORY_BATCH_SIZE]

    @staticmethod
    def _search_payload(
        search_term: str,
        project: Optional[str],
        repository_names: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Build a Code Search payload with optional scope filters."""
        payload: Dict[str, Any] = {"searchText": search_term}
        filters: Dict[str, List[str]] = {}
        if project:
            filters["Project"] = [project]
        if repository_names is not None:
            filters["Repository"] = repository_names
        if filters:
            payload["filters"] = filters
        return payload

    def _search_pages(
        self,
        url: str,
        params: Dict[str, str],
        payload: Dict[str, Any],
        max_results: int,
    ):
        """Yield Code Search pages until ``max_results`` have been fetched.

        Azure DevOps Code Search accepts ``$skip`` and ``$top`` in the request
        body.  The service currently trims a page to at most 1,000 results, so
        requests larger than that are split into multiple pages here.
        """
        if max_results <= 0:
            return

        skip = 0
        previous_page_signature = None
        while skip < max_results:
            page_size = min(CODE_SEARCH_PAGE_SIZE, max_results - skip)
            page_payload = dict(payload)
            page_payload["$top"] = page_size
            page_payload["$skip"] = skip

            try:
                response = requests.post(
                    url,
                    headers=self.auth.headers(),
                    json=page_payload,
                    params=params,
                    timeout=CODE_SEARCH_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                if skip:
                    raise Exception(
                        "Failed to fetch Code Search page at skip="
                        f"{skip}: {str(e)}. Azure DevOps may enforce its "
                        "1,000-result search boundary; use narrower "
                        "repository or path filters if this occurs."
                    ) from e
                raise

            results = data.get('results', [])
            if not results:
                return

            page_signature = tuple(
                (
                    result.get('project', {}).get('id'),
                    result.get('repository', {}).get('id'),
                    result.get('path'),
                    result.get('fileName'),
                )
                for result in results
            )
            if page_signature == previous_page_signature:
                raise Exception(
                    "Azure DevOps returned the same Code Search page twice "
                    f"at skip={skip}; pagination is not advancing."
                )

            yield data
            previous_page_signature = page_signature
            skip += len(results)

            if len(results) < page_size:
                return
