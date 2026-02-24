from unittest.mock import MagicMock

from gitlab_utils import (
    batch,
    commits,
    groups,
    issues,
    merge_requests,
    productivity_utils,
    projects,
    users,
)


def test_get_user_by_username_returns_first_match():
    client = MagicMock()
    client._get.return_value = [{"id": 10, "username": "alice"}, {"id": 20, "username": "alice"}]

    result = users.get_user_by_username(client, "alice")

    assert result == {"id": 10, "username": "alice"}
    client._get.assert_called_once_with("/users", params={"username": "alice"})


def test_get_user_by_username_returns_none_for_empty_response():
    client = MagicMock()
    client._get.return_value = []
    assert users.get_user_by_username(client, "alice") is None


def test_get_user_groups_deduplicates_and_maps_fields():
    client = MagicMock()
    client._get_paginated.return_value = [
        {"id": 1, "name": "A", "full_path": "org/a", "visibility": "private"},
        {"id": 1, "name": "A", "full_path": "org/a", "visibility": "private"},
        {"id": 2, "name": "B", "full_path": "org/b", "visibility": "public"},
    ]

    result = groups.get_user_groups(client, 42)

    assert result == [
        {"name": "A", "full_path": "org/a", "visibility": "private"},
        {"name": "B", "full_path": "org/b", "visibility": "public"},
    ]


def test_get_user_groups_returns_empty_on_exception():
    client = MagicMock()
    client._get_paginated.side_effect = RuntimeError("boom")
    assert groups.get_user_groups(client, 42) == []


def test_get_user_issues_counts_opened_closed():
    client = MagicMock()
    client._get_paginated.return_value = [
        {"title": "i1", "project_id": 1, "web_url": "u1", "state": "opened", "created_at": "t1"},
        {"title": "i2", "project_id": 2, "web_url": "u2", "state": "closed", "created_at": "t2"},
        {"title": "i3", "project_id": 3, "web_url": "u3", "state": "other", "created_at": "t3"},
    ]

    issue_list, stats = issues.get_user_issues(client, 10)

    assert len(issue_list) == 3
    assert stats == {"total": 3, "opened": 1, "closed": 1}


def test_get_user_issues_returns_defaults_on_exception():
    client = MagicMock()
    client._get_paginated.side_effect = RuntimeError("boom")

    issue_list, stats = issues.get_user_issues(client, 10)

    assert issue_list == []
    assert stats == {"total": 0, "opened": 0, "closed": 0}


def test_get_user_mrs_deduplicates_across_authored_and_assigned():
    client = MagicMock()
    authored = [
        {
            "id": 11,
            "title": "MR1",
            "project_id": 1,
            "web_url": "u1",
            "state": "merged",
            "created_at": "t1",
        },
        {
            "id": 12,
            "title": "MR2",
            "project_id": 1,
            "web_url": "u2",
            "state": "opened",
            "created_at": "t2",
        },
    ]
    assigned = [
        {
            "id": 12,
            "title": "MR2",
            "project_id": 1,
            "web_url": "u2",
            "state": "opened",
            "created_at": "t2",
        },
        {
            "id": 13,
            "title": "MR3",
            "project_id": 2,
            "web_url": "u3",
            "state": "closed",
            "created_at": "t3",
        },
    ]
    client._get_paginated.side_effect = [authored, assigned]

    mr_list, stats = merge_requests.get_user_mrs(client, 99)

    assert [m["title"] for m in mr_list] == ["MR1", "MR2", "MR3"]
    assert stats["total"] == 3
    assert stats["merged"] == 1
    assert stats["opened"] == 1
    assert stats["closed"] == 1
    assert stats["pending"] == 1


def test_get_user_projects_merges_event_projects_and_classifies():
    client = MagicMock()
    direct_projects = [
        {
            "id": 1,
            "namespace": {"path": "alice", "kind": "user"},
            "name": "p1",
        }
    ]
    events = [{"project_id": 2}, {"project_id": 2}, {"project_id": 3}]
    extra_p2 = {"id": 2, "namespace": {"path": "team", "kind": "group"}, "name": "p2"}
    extra_p3 = {"id": 3, "namespace": {"path": "bob", "kind": "user"}, "name": "p3"}

    client._get_paginated.side_effect = [direct_projects, events]
    client._get.side_effect = [extra_p2, extra_p3]

    result = projects.get_user_projects(client, 100, "alice")

    assert [p["id"] for p in result["personal"]] == [1]
    assert [p["id"] for p in result["contributed"]] == [2, 3]
    assert sorted(p["id"] for p in result["all"]) == [1, 2, 3]


def test_get_user_projects_returns_empty_buckets_on_error():
    client = MagicMock()
    client._get_paginated.side_effect = RuntimeError("boom")

    result = projects.get_user_projects(client, 100, "alice")

    assert result == {"personal": [], "contributed": [], "all": []}


def test_get_user_commits_filters_by_author_and_counts_time_slots():
    client = MagicMock()
    user = {"name": "Alice", "email": "alice@example.com", "username": "alice"}
    projects_input = [
        {"id": 1, "name_with_namespace": "A/p1"},
        {"id": 2, "name_with_namespace": "A/p2"},
    ]
    project1_commits = [
        {
            "id": "sha1",
            "title": "morning commit",
            "author_name": "Alice",
            "author_email": "alice@example.com",
            "created_at": "2026-01-01T05:00:00+00:00",
            "short_id": "sha1",
        },
        {
            "id": "sha2",
            "title": "afternoon commit",
            "author_name": "Alice",
            "author_email": "alice@example.com",
            "created_at": "2026-01-01T09:00:00+00:00",
            "short_id": "sha2",
        },
        {
            "id": "sha3",
            "title": "ignored commit",
            "author_name": "Other",
            "author_email": "other@example.com",
            "created_at": "2026-01-01T09:00:00+00:00",
            "short_id": "sha3",
        },
    ]
    project2_commits = [
        {
            "id": "sha2",
            "title": "duplicate across projects",
            "author_name": "Alice",
            "author_email": "alice@example.com",
            "created_at": "2026-01-01T09:00:00+00:00",
            "short_id": "sha2",
        }
    ]
    client._get_paginated.side_effect = [project1_commits, project2_commits]

    all_commits, project_counts, stats = commits.get_user_commits(client, user, projects_input)

    assert len(all_commits) == 2
    assert project_counts == {1: 2, 2: 1}
    assert stats["total"] == 2
    assert stats["morning_commits"] == 1
    assert stats["afternoon_commits"] == 1


def test_get_user_commits_ignores_project_exceptions():
    client = MagicMock()
    user = {"name": "Alice", "email": "alice@example.com", "username": "alice"}
    projects_input = [{"id": 1, "name_with_namespace": "A/p1"}]
    client._get_paginated.side_effect = RuntimeError("boom")

    all_commits, project_counts, stats = commits.get_user_commits(client, user, projects_input)

    assert all_commits == []
    assert project_counts == {}
    assert stats == {"total": 0, "morning_commits": 0, "afternoon_commits": 0}


def test_get_user_productivity_aggregates_stats(monkeypatch):
    monkeypatch.setattr(productivity_utils.users, "get_user_by_username", lambda *_: {"id": 7})
    monkeypatch.setattr(
        productivity_utils.projects, "get_user_projects", lambda *_: {"all": [{"id": 1}]}
    )
    monkeypatch.setattr(
        productivity_utils.commits, "get_user_commits", lambda *_: ([], {}, {"total": 9})
    )
    monkeypatch.setattr(
        productivity_utils.merge_requests, "get_user_mrs", lambda *_: ([], {"opened": 2, "closed": 1, "merged": 1})
    )
    monkeypatch.setattr(
        productivity_utils.issues, "get_user_issues", lambda *_: ([], {"opened": 3, "closed": 2})
    )

    stats = productivity_utils.get_user_productivity(MagicMock(), "alice")

    assert stats == {
        "username": "alice",
        "commits_count": 9,
        "mrs_opened": 2,
        "mrs_closed": 1,
        "mrs_merged": 1,
        "issues_opened": 3,
        "issues_closed": 2,
    }


def test_get_user_productivity_returns_none_when_user_missing(monkeypatch):
    monkeypatch.setattr(productivity_utils.users, "get_user_by_username", lambda *_: None)
    assert productivity_utils.get_user_productivity(MagicMock(), "alice") is None


def test_get_team_productivity_sums_member_stats(monkeypatch):
    responses = {
        "alice": {
            "username": "alice",
            "commits_count": 5,
            "mrs_opened": 2,
            "mrs_closed": 1,
            "mrs_merged": 1,
            "issues_opened": 3,
            "issues_closed": 2,
        },
        "bob": None,
        "carol": {
            "username": "carol",
            "commits_count": 7,
            "mrs_opened": 1,
            "mrs_closed": 2,
            "mrs_merged": 2,
            "issues_opened": 0,
            "issues_closed": 1,
        },
    }
    monkeypatch.setattr(productivity_utils, "get_user_productivity", lambda _c, m: responses[m])

    stats = productivity_utils.get_team_productivity(MagicMock(), "TeamX", ["alice", "bob", "carol"])

    assert stats["team_name"] == "TeamX"
    assert stats["total_commits"] == 12
    assert stats["total_mrs_opened"] == 3
    assert stats["total_mrs_closed"] == 3
    assert stats["total_mrs_merged"] == 3
    assert stats["total_issues_opened"] == 3
    assert stats["total_issues_closed"] == 3
    assert [m["username"] for m in stats["member_stats"]] == ["alice", "carol"]


def test_process_single_user_not_found(monkeypatch):
    monkeypatch.setattr(batch.users, "get_user_by_username", lambda *_: None)

    result = batch.process_single_user(MagicMock(), "alice")

    assert result["status"] == "Not Found"
    assert result["error"] == "User not found"


def test_process_single_user_filters_contributed_by_commit_counts(monkeypatch):
    user_obj = {"id": 1, "username": "alice", "name": "Alice"}
    projs = {
        "personal": [{"id": 10}],
        "contributed": [{"id": 20}, {"id": 30}],
        "all": [{"id": 10}, {"id": 20}, {"id": 30}],
    }
    monkeypatch.setattr(batch.users, "get_user_by_username", lambda *_: user_obj)
    monkeypatch.setattr(batch.projects, "get_user_projects", lambda *_: projs)
    monkeypatch.setattr(
        batch.commits,
        "get_user_commits",
        lambda *_: ([{"id": "c1"}], {20: 2, 30: 0}, {"total": 2, "morning_commits": 1, "afternoon_commits": 1}),
    )
    monkeypatch.setattr(batch.groups, "get_user_groups", lambda *_: [{"name": "g"}])
    monkeypatch.setattr(batch.merge_requests, "get_user_mrs", lambda *_: ([{"title": "mr"}], {"total": 1}))
    monkeypatch.setattr(batch.issues, "get_user_issues", lambda *_: ([{"title": "i"}], {"total": 1}))

    result = batch.process_single_user(MagicMock(), "alice")

    assert result["status"] == "Success"
    assert [p["id"] for p in result["data"]["projects"]["contributed"]] == [20]
    assert result["data"]["commit_stats"]["total"] == 2


def test_process_batch_users_ignores_empty_usernames(monkeypatch):
    calls = []

    def fake_process_single_user(_client, username):
        calls.append(username)
        return {"username": username, "status": "Success"}

    monkeypatch.setattr(batch, "process_single_user", fake_process_single_user)

    results = batch.process_batch_users(MagicMock(), [" alice ", " ", "", "bob"])

    assert sorted(calls) == ["alice", "bob"]
    assert sorted([r["username"] for r in results]) == ["alice", "bob"]
