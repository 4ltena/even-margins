from PIL import Image
from trim import AppState, should_process, format_notification, _image_signature


def _img(color):
    return Image.new("RGB", (10, 10), color)


def test_toggle_enabled_and_notify():
    s = AppState()
    assert s.enabled is True and s.notify is True
    s.toggle_enabled()
    s.toggle_notify()
    assert s.enabled is False and s.notify is False
    s.toggle_enabled()
    assert s.enabled is True


def test_stop_event_starts_unset():
    assert AppState().stop_event.is_set() is False


def test_should_process_fresh_image_when_enabled():
    s = AppState()
    assert should_process(s, _img((1, 2, 3))) is True


def test_should_process_false_when_disabled():
    s = AppState()
    s.toggle_enabled()  # -> disabled
    assert should_process(s, _img((1, 2, 3))) is False


def test_should_process_false_for_none():
    assert should_process(AppState(), None) is False


def test_should_process_skips_own_output():
    s = AppState()
    out = _img((9, 9, 9))
    s.last_output_sig = _image_signature(out)
    assert should_process(s, out) is False


def test_format_notification():
    assert format_notification((1280, 720), (1344, 756)) == "Normalized 1280x720 -> 1344x756"
