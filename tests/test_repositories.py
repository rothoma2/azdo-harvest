"""Tests for Azure DevOps repository listing utilities."""

from unittest.mock import Mock, patch

from azdo_harvest.repositories import list_repositories, write_repository_names


def _response(repositories, continuation=None):
    response = Mock()
    response.json.return_value = {"count": len(repositories), "value": repositories}
    response.headers = {}
    if continuation:
        response.headers["x-ms-continuationtoken"] = continuation
    return response


@patch("azdo_harvest.repositories.requests.get")
def test_lists_all_pages(mock_get):
    mock_get.side_effect = [
        _response([{"name": "repo-a"}], continuation="next"),
        _response([{"name": "repo-b"}]),
    ]
    auth = Mock()
    auth.headers.return_value = {"Authorization": "Bearer token"}

    repositories = list_repositories("org", project="project", auth=auth)

    assert [repo["name"] for repo in repositories] == ["repo-a", "repo-b"]
    assert mock_get.call_args_list[1].kwargs["params"]["continuationToken"] == "next"


def test_writes_repository_names(tmp_path):
    output_file = tmp_path / "repositories.txt"
    write_repository_names([{"name": "repo-a"}, {"name": "repo-b"}], str(output_file))
    assert output_file.read_text(encoding="utf-8") == "repo-a\nrepo-b\n"
