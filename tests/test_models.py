"""Tests for FileResult and RepositoryResult models."""

import pytest
from azdo_harvest.models import FileResult, RepositoryResult


class TestFileResult:
    """Tests for FileResult dataclass."""
    
    def test_file_result_creation(self):
        """Test creating a FileResult object."""
        file_result = FileResult(
            repository="test-repo",
            repository_id="repo-123",
            project="test-project",
            project_id="proj-456",
            filepath="/src/main.py",
            branch="main",
            commit_id="abc123",
            organization="test-org",
            filename="main.py"
        )
        
        assert file_result.repository == "test-repo"
        assert file_result.filepath == "/src/main.py"
        assert file_result.branch == "main"
        assert file_result.organization == "test-org"
    
    def test_get_download_url(self):
        """Test generating download URL."""
        file_result = FileResult(
            repository="my-repo",
            repository_id="repo-id-123",
            project="my-project",
            project_id="proj-id-456",
            filepath="/src/app.py",
            branch="develop",
            commit_id="commit-789",
            organization="my-org",
            filename="app.py"
        )
        
        url = file_result.get_download_url()
        
        assert "https://dev.azure.com/my-org/my-project" in url
        assert "repositories/repo-id-123/items" in url
        assert "path=/src/app.py" in url
        assert "versionDescriptor.version=develop" in url
        assert "includeContent=true" in url
        assert "api-version=7.1" in url
    
    def test_get_download_url_without_repo_id(self):
        """Test URL generation when repository ID is None."""
        file_result = FileResult(
            repository="my-repo",
            repository_id=None,
            project="my-project",
            project_id="proj-id",
            filepath="/test.txt",
            branch="main",
            commit_id=None,
            organization="org",
            filename="test.txt"
        )
        
        url = file_result.get_download_url()
        assert "repositories/my-repo/items" in url
    
    def test_get_download_params(self):
        """Test getting download parameters."""
        file_result = FileResult(
            repository="repo",
            repository_id="id",
            project="proj",
            project_id="pid",
            filepath="/file.txt",
            branch="master",
            commit_id="commit",
            organization="org",
            filename="file.txt"
        )
        
        params = file_result.get_download_params()
        
        assert params["path"] == "/file.txt"
        assert params["versionDescriptor.version"] == "master"
        assert params["includeContent"] == "true"
        assert params["api-version"] == "7.1"
    
    def test_str_representation(self):
        """Test string representation."""
        file_result = FileResult(
            repository="my-repo",
            repository_id="id",
            project="proj",
            project_id="pid",
            filepath="/src/code.py",
            branch="main",
            commit_id="commit",
            organization="org",
            filename="code.py"
        )
        
        str_repr = str(file_result)
        assert "my-repo:/src/code.py" in str_repr
        assert "main" in str_repr


class TestRepositoryResult:
    """Tests for RepositoryResult dataclass."""
    
    def test_repository_result_creation(self):
        """Test creating a RepositoryResult object."""
        repo = RepositoryResult(
            name="test-repo",
            project="test-project",
            url="https://example.com/repo",
            repository_id="repo-123"
        )
        
        assert repo.name == "test-repo"
        assert repo.project == "test-project"
        assert repo.url == "https://example.com/repo"
        assert repo.repository_id == "repo-123"
    
    def test_repository_result_without_id(self):
        """Test creating RepositoryResult without ID."""
        repo = RepositoryResult(
            name="repo",
            project="proj",
            url="http://url"
        )
        
        assert repo.repository_id is None
    
    def test_str_representation(self):
        """Test string representation."""
        repo = RepositoryResult(
            name="my-repo",
            project="my-project",
            url="http://url"
        )
        
        str_repr = str(repo)
        assert "my-project/my-repo" == str_repr
