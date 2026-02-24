from user_profile import profile_utils


def test_parse_gitlab_datetime_handles_z_and_converts_to_ist():
    dt = profile_utils.parse_gitlab_datetime("2026-01-01T06:30:00Z")
    assert dt is not None
    assert dt.hour == 12
    assert dt.minute == 0


def test_parse_gitlab_datetime_returns_none_for_invalid_input():
    assert profile_utils.parse_gitlab_datetime("not-a-date") is None
    assert profile_utils.parse_gitlab_datetime(None) is None


def test_classify_time_slot_boundaries():
    assert profile_utils.classify_time_slot("2026-01-01T03:30:00Z") == "Morning"  # 09:00 IST
    assert profile_utils.classify_time_slot("2026-01-01T07:00:00Z") == "Morning"  # 12:30 IST
    assert profile_utils.classify_time_slot("2026-01-01T08:30:00Z") == "Afternoon"  # 14:00 IST
    assert profile_utils.classify_time_slot("2026-01-01T08:30:00+05:30") == "Other"  # 08:30 IST
    assert profile_utils.classify_time_slot("2026-01-01T11:30:00+05:30") == "Morning"
    assert profile_utils.classify_time_slot("2026-01-01T12:31:00+05:30") == "Other"


def test_format_date_time_invalid_returns_placeholders():
    assert profile_utils._format_date_time("bad") == ("-", "-")


def test_process_commits_maps_fields_and_skips_unparseable():
    commits = [
        {
            "project_scope": "personal",
            "project_name": "proj-a",
            "title": "feat: add test",
            "created_at": "2026-01-01T03:30:00Z",
        },
        {
            "project_scope": "contributed",
            "project_name": "proj-b",
            "message": "fix bug\nsecond line",
            "committed_date": "2026-01-01T08:30:00+05:30",
        },
        {
            "project_name": "proj-c",
            "title": "bad date",
            "created_at": "invalid",
        },
    ]

    rows = profile_utils.process_commits(commits)

    assert len(rows) == 2
    assert rows[0]["project_type"] == "personal"
    assert rows[0]["project"] == "proj-a"
    assert rows[0]["message"] == "feat: add test"
    assert rows[0]["slot"] == "Morning"
    assert rows[1]["message"] == "fix bug"
    assert rows[1]["slot"] == "Other"


def test_process_groups_with_fallback_keys():
    rows = profile_utils.process_groups(
        [
            {
                "name": "Core",
                "path": "core",
                "visibility": "private",
                "web_url": "https://example.com/core",
            },
            {},
        ]
    )
    assert rows[0]["path"] == "core"
    assert rows[1] == {"name": "-", "path": "-", "visibility": "-", "web_url": "-"}


def test_split_projects_personal_vs_contributed():
    user_info = {"username": "Alice", "id": 42}
    projects = [
        {"id": 1, "namespace": {"full_path": "alice"}},
        {"id": 2, "creator_id": 42},
        {"id": 3, "namespace": {"full_path": "team/shared"}, "creator_id": 7},
    ]

    personal, contributed = profile_utils.split_projects(projects, user_info)

    assert [p["id"] for p in personal] == [1, 2]
    assert [p["id"] for p in contributed] == [3]
