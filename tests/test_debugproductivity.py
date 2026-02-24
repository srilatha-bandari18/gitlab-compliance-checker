import pytest
from unittest.mock import MagicMock

import debugproductivity


def test_get_user_productivity_returns_none_without_token(capsys):
    result = debugproductivity.get_user_productivity("alice", gitlab_token="")

    captured = capsys.readouterr()
    assert result is None
    assert "GITLAB_TOKEN not found" in captured.out


def test_get_user_productivity_returns_none_when_client_init_fails(monkeypatch, capsys):
    mock_client = MagicMock()
    mock_client.client = None
    monkeypatch.setattr(debugproductivity, "GitLabClient", lambda *_args: mock_client)

    result = debugproductivity.get_user_productivity(
        "alice",
        gitlab_url="https://example.com",
        gitlab_token="token",
    )

    captured = capsys.readouterr()
    assert result is None
    assert "Failed to initialize GitLab client" in captured.out


def test_get_user_productivity_returns_none_when_user_not_found(monkeypatch, capsys):
    mock_client = MagicMock()
    mock_client.client = object()
    monkeypatch.setattr(debugproductivity, "GitLabClient", lambda *_args: mock_client)
    monkeypatch.setattr(debugproductivity.users, "get_user_by_username", lambda *_args: None)

    result = debugproductivity.get_user_productivity(
        "alice",
        gitlab_url="https://example.com",
        gitlab_token="token",
    )

    captured = capsys.readouterr()
    assert result is None
    assert "User 'alice' not found." in captured.out


def test_get_user_productivity_builds_expected_stats(monkeypatch):
    mock_client = MagicMock()
    mock_client.client = object()
    monkeypatch.setattr(debugproductivity, "GitLabClient", lambda *_args: mock_client)
    monkeypatch.setattr(
        debugproductivity.users,
        "get_user_by_username",
        lambda *_args: {"id": 42, "username": "alice"},
    )
    monkeypatch.setattr(
        debugproductivity.projects,
        "get_user_projects",
        lambda *_args: {"all": [{"id": 1}, {"id": 2}]},
    )
    monkeypatch.setattr(
        debugproductivity.merge_requests,
        "get_user_mrs",
        lambda *_args: ([], {"opened": 3, "closed": 2, "merged": 1}),
    )
    monkeypatch.setattr(
        debugproductivity.issues,
        "get_user_issues",
        lambda *_args: ([], {"opened": 4, "closed": 2}),
    )
    monkeypatch.setattr(
        debugproductivity.commits,
        "get_user_commits",
        lambda *_args: ([], {}, {"total": 7, "morning_commits": 5, "afternoon_commits": 2}),
    )

    stats = debugproductivity.get_user_productivity(
        "alice",
        gitlab_url="https://example.com",
        gitlab_token="token",
    )

    assert stats == {
        "username": "alice",
        "user_id": 42,
        "projects_count": 2,
        "commits": {"total": 7, "morning": 5, "afternoon": 2},
        "merge_requests": {"opened": 3, "closed": 2, "merged": 1},
        "issues": {"opened": 4, "closed": 2},
    }


def test_get_user_productivity_defaults_missing_stats_to_zero(monkeypatch):
    mock_client = MagicMock()
    mock_client.client = object()
    monkeypatch.setattr(debugproductivity, "GitLabClient", lambda *_args: mock_client)
    monkeypatch.setattr(
        debugproductivity.users,
        "get_user_by_username",
        lambda *_args: {"id": 42, "username": "alice"},
    )
    monkeypatch.setattr(
        debugproductivity.projects,
        "get_user_projects",
        lambda *_args: {"all": []},
    )
    monkeypatch.setattr(debugproductivity.merge_requests, "get_user_mrs", lambda *_args: ([], {}))
    monkeypatch.setattr(debugproductivity.issues, "get_user_issues", lambda *_args: ([], {}))
    monkeypatch.setattr(debugproductivity.commits, "get_user_commits", lambda *_args: ([], {}, {}))

    stats = debugproductivity.get_user_productivity(
        "alice",
        gitlab_url="https://example.com",
        gitlab_token="token",
    )

    assert stats["projects_count"] == 0
    assert stats["commits"] == {"total": 0, "morning": 0, "afternoon": 0}
    assert stats["merge_requests"] == {"opened": 0, "closed": 0, "merged": 0}
    assert stats["issues"] == {"opened": 0, "closed": 0}


def test_print_productivity_stats_formats_output(capsys):
    stats = {
        "username": "alice",
        "user_id": 42,
        "projects_count": 2,
        "commits": {"total": 7, "morning": 5, "afternoon": 2},
        "merge_requests": {"opened": 3, "closed": 2, "merged": 1},
        "issues": {"opened": 4, "closed": 2},
    }

    debugproductivity.print_productivity_stats(stats)
    out = capsys.readouterr().out

    assert "SUMMARY FOR: alice" in out
    assert "User ID:        42" in out
    assert "Total Commits:    7" in out
    assert "MRs Merged:     1" in out
    assert "Issues Closed:  2" in out


def test_main_exits_with_usage_when_args_missing(monkeypatch, capsys):
    monkeypatch.setattr(debugproductivity.sys, "argv", ["debugproductivity.py"])

    with pytest.raises(SystemExit) as exc:
        debugproductivity.main()

    out = capsys.readouterr().out
    assert exc.value.code == 1
    assert "Usage: python3 debugproductivity.py <gitlab_url> <username>" in out

