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
