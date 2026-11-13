"""Tests for Azure DevOps search pagination."""

from unittest.mock import Mock, patch

from azdo_harvest.search import AzureDevOpsSearcher


def _result(number):
    return {
        "fileName": f"file-{number}.txt",
        "path": f"/file-{number}.txt",
        "repository": {
            "id": "repo-id",
            "name": "repo",
        },
        "project": {
            "id": "project-id",
            "name": "project",
        },
        "versions": [{
            "branchName": "refs/heads/main",
            "changeId": f"commit-{number}",
        }],
    }


def _response(results):
    response = Mock()
    response.json.return_value = {"count": len(results), "results": results}
    return response


@patch("azdo_harvest.search.CODE_SEARCH_PAGE_SIZE", 1)
@patch("azdo_harvest.search.requests.post")
def test_code_search_paginates_beyond_1000_results(mock_post):
    mock_post.side_effect = [
        _response([_result(1)]),
        _response([_result(2)]),
        _response([]),
    ]
    searcher = AzureDevOpsSearcher("org", "project", "pat")

    results = searcher.search(
        "term", search_repos=False, max_results=2000
    )

    assert [result.filename for result in results["files"]] == [
        "file-1.txt", "file-2.txt"
    ]
    assert [call.kwargs["json"]["$skip"] for call in mock_post.call_args_list] == [
        0, 1, 2
    ]
    assert [call.kwargs["json"]["$top"] for call in mock_post.call_args_list] == [
        1, 1, 1
    ]


@patch("azdo_harvest.search.requests.post")
def test_repository_list_is_searched_in_batches_and_combined(mock_post):
    mock_post.side_effect = [
        _response([{
            "repository": {
                "id": "repo-1",
                "name": "repo-1",
                "remoteUrl": "https://example/repo-1",
            },
            "project": {"id": "project-id", "name": "project"},
        }]),
        _response([{
            "repository": {
                "id": "repo-901",
                "name": "repo-901",
                "remoteUrl": "https://example/repo-901",
            },
            "project": {"id": "project-id", "name": "project"},
        }]),
    ]
    searcher = AzureDevOpsSearcher("org", "project", "pat")

    results = searcher.search(
        "term",
        search_files=False,
        max_results=10,
        repository_names=[f"repo-{number}" for number in range(1, 902)],
    )

    assert [repo["name"] for repo in results["repositories"]] == [
        "repo-1", "repo-901"
    ]
    filters = [call.kwargs["json"]["filters"] for call in mock_post.call_args_list]
    assert len(filters[0]["Repository"]) == 500
    assert len(filters[1]["Repository"]) == 401


@patch("azdo_harvest.search.CODE_SEARCH_PAGE_SIZE", 2)
@patch("azdo_harvest.search.requests.post")
def test_code_search_deduplicates_overlapping_pages(mock_post):
    mock_post.side_effect = [
        _response([_result(1), _result(2)]),
        _response([_result(2), _result(3)]),
    ]
    searcher = AzureDevOpsSearcher("org", "project", "pat")

    results = searcher.search(
        "term", search_repos=False, max_results=4
    )

    assert [result.filename for result in results["files"]] == [
        "file-1.txt", "file-2.txt", "file-3.txt"
    ]
    assert [call.kwargs["json"]["$skip"] for call in mock_post.call_args_list] == [
        0, 2
    ]
