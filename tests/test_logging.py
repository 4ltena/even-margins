import os

import trim


def test_default_log_path_is_next_to_module():
    expected = os.path.join(os.path.dirname(os.path.abspath(trim.__file__)), "even-margins.log")
    assert trim.default_log_path() == expected


def test_setup_logging_writes_to_file_and_is_idempotent(tmp_path):
    logfile = tmp_path / "t.log"
    lg = trim.setup_logging(str(logfile), name="even-margins-test")
    handler_count = len(lg.handlers)
    lg2 = trim.setup_logging(str(logfile), name="even-margins-test")
    assert lg2 is lg
    assert len(lg2.handlers) == handler_count  # second call adds no duplicate handlers
    lg.info("hello-logfile")
    for h in lg.handlers:
        h.flush()
    assert "hello-logfile" in logfile.read_text(encoding="utf-8")
