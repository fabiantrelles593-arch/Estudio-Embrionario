import subprocess

from geovida.provenance import git_state


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                        "PATH": "/usr/bin:/bin"})


def _repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "docs" / "n.md").write_text("nota\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def test_clean_tree_reports_commit_and_not_dirty(tmp_path):
    repo = _repo(tmp_path)
    s = git_state(repo)
    assert len(s["commit"]) == 40 and s["dirty_code"] is False


def test_editing_tracked_code_marks_dirty(tmp_path):
    repo = _repo(tmp_path)
    (repo / "src" / "a.py").write_text("x = 2\n")
    assert git_state(repo)["dirty_code"] is True


def test_editing_docs_or_adding_results_does_not_mark_dirty(tmp_path):
    repo = _repo(tmp_path)
    (repo / "docs" / "n.md").write_text("otra nota\n")
    (repo / "results.csv").write_text("a,b\n")
    assert git_state(repo)["dirty_code"] is False


def test_outside_a_repository_is_unknown(tmp_path):
    s = git_state(tmp_path)
    assert s["commit"] == "unknown" and s["dirty_code"] is None
