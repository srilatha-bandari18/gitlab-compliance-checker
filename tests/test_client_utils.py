import requests #for requests
import sys
from types import ModuleType
from unittest.mock import MagicMock


# Provide lightweight stubs so importing gitlab_utils.client does not require
# full third-party packages in minimal test environments.
if "streamlit" not in sys.modules:
    streamlit_stub = ModuleType("streamlit")
    streamlit_stub.error = lambda *_args, **_kwargs: None
    streamlit_stub.cache_data = lambda *args, **kwargs: (lambda f: f)
    sys.modules["streamlit"] = streamlit_stub

if "gitlab" not in sys.modules:
    gitlab_stub = ModuleType("gitlab")

    class _Gitlab:
        def __init__(self, *args, **kwargs):
            pass

        def auth(self):
            return None

    class _Exceptions:
        class GitlabAuthenticationError(Exception):
            pass

        class GitlabConnectionError(Exception):
            pass

    class GitlabGetError(Exception):
        pass

    gitlab_stub.Gitlab = _Gitlab
    gitlab_stub.exceptions = _Exceptions
    gitlab_stub.GitlabGetError = GitlabGetError
    sys.modules["gitlab"] = gitlab_stub

from gitlab_utils import client as client_mod


def test_safe_api_call_returns_result_on_success():
    assert client_mod.safe_api_call(lambda x: x + 1, 1) == 2


def test_safe_api_call_retries_and_returns_empty_on_connection_errors(monkeypatch):
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        raise requests.exceptions.ConnectionError("network")

    result = client_mod.safe_api_call(flaky)

    assert result == []
    assert attempts["n"] == 3


def test_safe_api_call_returns_empty_on_unexpected_errors():
    result = client_mod.safe_api_call(lambda: (_ for _ in ()).throw(ValueError("bad")))
    assert result == []


def test_get_paginated_collects_until_short_page():
    instance = client_mod.GitLabClient.__new__(client_mod.GitLabClient)
    instance._get = MagicMock(
        side_effect=[
            [{"id": 1}, {"id": 2}],
            [{"id": 3}],
        ]
    )

    rows = instance._get_paginated("/projects", params={"a": 1}, per_page=2, max_pages=5)

    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert instance._get.call_count == 2


def test_get_paginated_stops_on_non_list_response():
    instance = client_mod.GitLabClient.__new__(client_mod.GitLabClient)
    instance._get = MagicMock(return_value={"unexpected": True})

    rows = instance._get_paginated("/projects", per_page=2, max_pages=5)
    assert rows == []
