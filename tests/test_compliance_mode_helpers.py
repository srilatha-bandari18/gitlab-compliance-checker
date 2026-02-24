import sys
from types import SimpleNamespace
from types import ModuleType
from unittest.mock import MagicMock


if "streamlit" not in sys.modules:
    streamlit_stub = ModuleType("streamlit")
    streamlit_stub.cache_data = lambda *args, **kwargs: (lambda f: f)
    streamlit_stub.subheader = lambda *_args, **_kwargs: None
    streamlit_stub.markdown = lambda *_args, **_kwargs: None
    streamlit_stub.write = lambda *_args, **_kwargs: None
    streamlit_stub.error = lambda *_args, **_kwargs: None
    streamlit_stub.columns = lambda *args, **kwargs: []
    sys.modules["streamlit"] = streamlit_stub

if "gitlab" not in sys.modules:
    gitlab_stub = ModuleType("gitlab")

    class GitlabGetError(Exception):
        pass

    gitlab_stub.GitlabGetError = GitlabGetError
    sys.modules["gitlab"] = gitlab_stub

from modes import compliance_mode


def test_extract_path_from_url_handles_git_suffix_and_plain_text():
    assert (
        compliance_mode.extract_path_from_url("https://gitlab.com/group/project.git")
        == "group/project"
    )
    assert compliance_mode.extract_path_from_url("https://gitlab.com/group/project") == "group/project"
    assert compliance_mode.extract_path_from_url(" group/project ") == "group/project"


def test_get_project_branches_sorted_and_fallback():
    project = MagicMock()
    project.branches.list.return_value = [SimpleNamespace(name="dev"), SimpleNamespace(name="main")]

    branches = compliance_mode.get_project_branches(project)
    assert branches == ["dev", "main"]

    project.branches.list.side_effect = RuntimeError("boom")
    assert compliance_mode.get_project_branches(project) == []


def test_check_extensions_json_for_ruff(monkeypatch):
    monkeypatch.setattr(
        compliance_mode,
        "read_file_content",
        lambda *_: '{"recommendations":["ms-python.python","charliermarsh.ruff"]}',
    )
    assert compliance_mode.check_extensions_json_for_ruff(MagicMock(), "main") is True

    monkeypatch.setattr(
        compliance_mode,
        "read_file_content",
        lambda *_: '{"recommendations":["company.RUFF-Linter"]}',
    )
    assert compliance_mode.check_extensions_json_for_ruff(MagicMock(), "main") is True

    monkeypatch.setattr(compliance_mode, "read_file_content", lambda *_: '{"recommendations":["ms-python.python"]}')
    assert compliance_mode.check_extensions_json_for_ruff(MagicMock(), "main") is False


def test_check_templates_presence_detects_markdown_templates():
    project = MagicMock()

    def tree(path, ref):
        if path == ".gitlab/issue_templates":
            return [{"name": "bug.md"}, {"name": "notes.txt"}]
        if path == ".gitlab/merge_request_templates":
            return [{"name": "mr_template.MD"}]
        return []

    project.repository_tree.side_effect = tree
    result = compliance_mode.check_templates_presence(project, "main")

    assert result["issue_templates_folder"] is True
    assert result["issue_template_files"] == ["bug.md"]
    assert result["merge_request_templates_folder"] is True
    assert result["merge_request_template_files"] == ["mr_template.MD"]


def test_check_license_content_statuses(monkeypatch):
    valid_agpl = (
        "GNU AFFERO GENERAL PUBLIC LICENSE\n"
        "Version 3, 19 November 2007"
    )
    gplv3 = "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"
    mit = "MIT License Copyright (c)"

    monkeypatch.setattr(compliance_mode, "read_file_content", lambda *_: valid_agpl)
    assert compliance_mode.check_license_content(MagicMock(), "main") == "valid"

    monkeypatch.setattr(compliance_mode, "read_file_content", lambda *_: gplv3)
    assert compliance_mode.check_license_content(MagicMock(), "main") == "gnu_other"

    monkeypatch.setattr(compliance_mode, "read_file_content", lambda *_: mit)
    assert compliance_mode.check_license_content(MagicMock(), "main") == "invalid"

    monkeypatch.setattr(compliance_mode, "read_file_content", lambda *_: None)
    assert compliance_mode.check_license_content(MagicMock(), "main") == "not_found"


def test_check_project_compliance_happy_path(monkeypatch):
    project = MagicMock()
    project.default_branch = "main"
    project.description = "A sample project"
    project.tags.list.return_value = [MagicMock()]

    def tree(path=None, ref=None):
        if path is None:
            return [
                {"name": "README.md"},
                {"name": "CONTRIBUTING.md"},
                {"name": "CHANGELOG.md"},
                {"name": "LICENSE"},
                {"name": ".gitignore"},
                {"name": "pyproject.toml"},
                {"name": "uv.lock"},
            ]
        if path == ".vscode":
            return [
                {"name": "settings.json"},
                {"name": "extensions.json"},
                {"name": "launch.json"},
                {"name": "tasks.json"},
            ]
        if path == ".gitlab/issue_templates":
            return [{"name": "bug.md"}]
        if path == ".gitlab/merge_request_templates":
            return [{"name": "mr.md"}]
        return []

    project.repository_tree.side_effect = tree

    def read_file_side_effect(_project, file_path, _branch):
        if file_path == "README.md":
            return (
                "Installation\nUsage\nLicense\nContributing\n"
                + ("x" * 200)
            )
        if file_path in {"LICENSE", "LICENSE.md"}:
            return "GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007"
        if file_path == ".vscode/settings.json":
            return "{}"
        if file_path == ".vscode/extensions.json":
            return '{"recommendations":["charliermarsh.ruff"]}'
        return None

    monkeypatch.setattr(compliance_mode, "read_file_content", read_file_side_effect)
    report = compliance_mode.check_project_compliance(project, "main")

    assert report["README.md"] is True
    assert report["CONTRIBUTING.md"] is True
    assert report["CHANGELOG"] is True
    assert report["LICENSE"] is True
    assert report["license_valid"] is True
    assert report["readme_status"] == "present"
    assert report["readme_needs_improvement"] is False
    assert report["vscode_settings"] is True
    assert report["vscode_extensions_exists"] is True
    assert report["vscode_launch_exists"] is True
    assert report["vscode_tasks_exists"] is True
    assert report["vscode_ruff_in_extensions"] is True
    assert report["description_present"] is True
    assert report["tags_present"] is True
    assert report["issue_templates_folder"] is True
    assert report["merge_request_templates_folder"] is True


def test_get_suggestions_for_missing_items_calls_streamlit(monkeypatch):
    calls = {"subheader": [], "markdown": []}
    fake_st = MagicMock()
    fake_st.subheader.side_effect = lambda text: calls["subheader"].append(text)
    fake_st.markdown.side_effect = lambda text: calls["markdown"].append(text)
    monkeypatch.setattr(compliance_mode, "st", fake_st)

    report = {
        "README.md": False,
        "license_valid": False,
        "readme_status": "empty",
        "readme_needs_improvement": True,
    }
    compliance_mode.get_suggestions_for_missing_items(report)

    assert calls["subheader"]
    joined = "\n".join(calls["markdown"])
    assert "README.md missing" in joined
    assert "LICENSE is not AGPLv3" in joined
    assert "README is empty" in joined
