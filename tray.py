"""System-tray UI for even-margins: enable/disable, notifications toggle, quit."""

import threading

import trim


def notify_toast(text):
    """Show a Windows toast. Never raises; degrades to a no-op if unavailable."""
    try:
        from windows_toasts import Toast, WindowsToaster

        toaster = WindowsToaster("even-margins")
        toast = Toast()
        toast.text_fields = [text]
        toaster.show_toast(toast)
    except Exception:
        pass


def _make_icon_image():
    """Generate a simple tray icon (a framed rectangle) with PIL, no shipped asset."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (64, 64), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([14, 20, 50, 44], outline=(240, 240, 240), width=3)
    return img


def _quit(icon, state):
    state.stop_event.set()
    icon.stop()


def make_tray_icon(state, config):
    """Build the pystray icon with the Enabled / Notifications / Quit menu."""
    import pystray
    from pystray import MenuItem as Item

    menu = pystray.Menu(
        Item("Enabled", lambda icon, item: state.toggle_enabled(),
             checked=lambda item: state.enabled),
        Item("Notifications", lambda icon, item: state.toggle_notify(),
             checked=lambda item: state.notify),
        Item("Quit", lambda icon, item: _quit(icon, state)),
    )
    return pystray.Icon("even-margins", _make_icon_image(), "even-margins", menu)


def run(config):
    """Start the watcher thread and run the tray icon on the main thread."""
    state = trim.AppState(enabled=True, notify=config.get("notify", True))
    worker = threading.Thread(
        target=trim.watch_clipboard,
        args=(state, config, notify_toast),
        daemon=True,
    )
    worker.start()
    make_tray_icon(state, config).run()
