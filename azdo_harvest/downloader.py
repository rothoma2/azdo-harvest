"""File download functionality for Azure DevOps."""
import requests
from pathlib import Path
from typing import Optional
from azdo_harvest.models import FileResult


class FileDownloader:
    """Download files from Azure DevOps using the Git Items API."""

    def __init__(self, headers: dict):
        """Initialize the file downloader.

        Args:
            headers: Authentication headers to use for API requests
        """
        self.headers = headers

    def download_file(
        self,
        file_result: FileResult,
        output_dir: Optional[str] = None,
        preserve_structure: bool = True,
        custom_filename: Optional[str] = None
    ) -> str:
        """Download a file from Azure DevOps.

        Uses the Git Items API:
        GET https://dev.azure.com/{org}/{project}/_apis/git/repositories/
        {repoId}/items

        Args:
            file_result: FileResult object with download information
            output_dir: Directory to save file (default: current directory)
            preserve_structure: If True, preserve repository path structure
            custom_filename: Optional custom filename (overrides
                preserve_structure)

        Returns:
            Path to the downloaded file
        """
        url = file_result.get_download_url()

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            if output_dir:
                base_path = Path(output_dir)
            else:
                base_path = Path.cwd()

            if custom_filename:
                file_path = base_path / custom_filename
            elif preserve_structure:
                repo_path = file_result.repository
                file_subpath = file_result.filepath.lstrip('/')
                file_path = base_path / repo_path / file_subpath
            else:
                file_path = base_path / file_result.filename

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(response.text, encoding='utf-8')

            return str(file_path)

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to download {file_result.filepath}: {str(e)}"
            )

    def download_files(
        self,
        file_results: list[FileResult],
        output_dir: Optional[str] = None,
        preserve_structure: bool = True
    ) -> dict[str, str]:
        """Download multiple files from Azure DevOps.

        Args:
            file_results: List of FileResult objects
            output_dir: Directory to save files (default: current directory)
            preserve_structure: If True, preserve repository path structure

        Returns:
            Dictionary mapping source path to downloaded file path
        """
        downloaded = {}

        for file_result in file_results:
            try:
                output_path = self.download_file(
                    file_result,
                    output_dir,
                    preserve_structure
                )
                downloaded[str(file_result)] = output_path
            except Exception as e:
                print(f"Error downloading {file_result}: {e}")
                downloaded[str(file_result)] = None

        return downloaded

    def get_file_content(self, file_result: FileResult) -> str:
        """Get file content without saving to disk.

        Args:
            file_result: FileResult object with download information

        Returns:
            File content as string
        """
        url = file_result.get_download_url()

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to get content for {file_result.filepath}: "
                f"{str(e)}"
            )
