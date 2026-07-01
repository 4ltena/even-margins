import os

import trim
from trim import load_config


def test_default_config_path_is_next_to_module():
    expected = os.path.join(os.path.dirname(os.path.abspath(trim.__file__)), "config.toml")
    assert trim.default_config_path() == expected


def test_load_config_default_ignores_cwd(monkeypatch, tmp_path):
    # A config.toml sitting in the current working directory must be ignored;
    # the default path is resolved next to trim.py, not from the CWD.
    (tmp_path / "config.toml").write_text("ratio = 0.99\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg["ratio"] != 0.99


def test_missing_file_returns_defaults():
    cfg = load_config("does_not_exist.toml")
    assert cfg == {
        "ratio": 0.05,
        "poll_interval": 0.3,
        "tolerance": 20,
        "corner_size": 8,
        "notify": True,
    }


def test_partial_file_is_merged_with_defaults(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('ratio = 0.2\n', encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg["ratio"] == 0.2
    assert cfg["poll_interval"] == 0.3
    assert cfg["tolerance"] == 20
    assert cfg["corner_size"] == 8
    assert cfg["notify"] is True


def test_malformed_file_returns_defaults(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("ratio = = =\n", encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg == {
        "ratio": 0.05,
        "poll_interval": 0.3,
        "tolerance": 20,
        "corner_size": 8,
        "notify": True,
    }
