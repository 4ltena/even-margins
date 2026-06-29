from trim import load_config


def test_missing_file_returns_defaults():
    cfg = load_config("does_not_exist.toml")
    assert cfg == {
        "ratio": 0.05,
        "hotkey": "ctrl+alt+s",
        "tolerance": 20,
        "corner_size": 8,
    }


def test_partial_file_is_merged_with_defaults(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('ratio = 0.2\n', encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg["ratio"] == 0.2
    assert cfg["hotkey"] == "ctrl+alt+s"
    assert cfg["tolerance"] == 20
    assert cfg["corner_size"] == 8


def test_malformed_file_returns_defaults(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("ratio = = =\n", encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg == {
        "ratio": 0.05,
        "hotkey": "ctrl+alt+s",
        "tolerance": 20,
        "corner_size": 8,
    }
