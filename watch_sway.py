# watch_sway.py — resilient version
# deps: python3, i3ipc, hidapi; mx_master_4.py in the same folder

import time, signal, sys
import i3ipc, hid
import mx_master_4

# Your known slot on the Bolt receiver
DEVICE_IDX = 2

# Haptic pattern & spam control
PATTERN  = 1      # try 0..14 for feel
COOLDOWN = 0.7    # seconds

LOGI_VID     = 0x046D
BOLT_PID     = 0xC548
USAGE_PREFS  = (0xFF00, 0x01, 0x0C)  # try HID++-ish iface first, then others

mx_ctx = None
mx     = None
_last  = 0.0

def find_bolt_hidpp_path():
    """
    Re-scan all Logitech Bolt interfaces and pick a candidate to open.
    Prefer usage_page 0xFF00; fallback to others if needed.
    Returns a string path like '/dev/hidraw5' or raises RuntimeError.
    """
    cands = []
    for d in hid.enumerate():
        if d.get('vendor_id') == LOGI_VID and d.get('product_id') == BOLT_PID:
            p = d['path']
            if isinstance(p, (bytes, bytearray)):
                p = p.decode()
            cands.append((p, d.get('usage_page')))
    if not cands:
        raise RuntimeError("Bolt receiver (046D:C548) not found")

    # sort by preferred usage pages
    def prio(u):
        try:
            return USAGE_PREFS.index(u)
        except ValueError:
            return len(USAGE_PREFS) + 1
    cands.sort(key=lambda t: prio(t[1]))
    return cands[0][0]

def open_device():
    """Open (or reopen) the HID++ device context and return (ctx, dev)."""
    global mx_ctx, mx
    # close old one if present
    if mx_ctx is not None:
        try:
            mx_ctx.__exit__(None, None, None)
        except Exception:
            pass
        mx_ctx = None
    path = find_bolt_hidpp_path()
    ctx = mx_master_4.MXMaster4(path=path, device_idx=DEVICE_IDX)
    dev = ctx.__enter__()
    return ctx, dev

def ensure_open(backoff=0.5, max_wait=8.0):
    """Ensure mx is open; if not, try to reopen with exponential backoff."""
    global mx_ctx, mx
    if mx is not None:
        return
    delay = backoff
    start = time.time()
    while True:
        try:
            mx_ctx, mx = open_device()
            # quick self-test (ignore errors)
            try:
                mx.hidpp(mx_master_4.FunctionID.Haptic, PATTERN)
            except Exception:
                pass
            print("HID++ opened.")
            return
        except Exception as e:
            mx_ctx, mx = None, None
            if time.time() - start > max_wait:
                # keep retrying slowly in the background
                print(f"Reopen failed ({e}); will keep trying…")
                time.sleep(delay)
                delay = min(delay * 2, 5.0)
            else:
                time.sleep(delay)
                delay = min(delay * 2, 2.0)

def buzz():
    """Send one haptic; if the pipe is broken, reopen and retry once."""
    global mx
    if time.time() - _last < COOLDOWN:
        return
    ensure_open()
    try:
        mx.hidpp(mx_master_4.FunctionID.Haptic, PATTERN)
        return True
    except Exception as e:
        # broken pipe / device vanished -> reopen and retry once
        print("haptic error (will reopen):", e)
        try:
            # mark closed
            if mx_ctx is not None:
                mx_ctx.__exit__(None, None, None)
        except Exception:
            pass
        finally:
            # clear handles and reopen
            reset_handles()
            ensure_open()
            try:
                mx.hidpp(mx_master_4.FunctionID.Haptic, PATTERN)
                return True
            except Exception as e2:
                print("haptic error after reopen:", e2)
                return False

def reset_handles():
    global mx_ctx, mx
    mx_ctx, mx = None, None

def on_window_focus(_i3, _event):
    global _last
    if buzz():
        _last = time.time()

def cleanup(*_):
    try:
        if mx_ctx is not None:
            mx_ctx.__exit__(None, None, None)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    # open lazily on first buzz; or uncomment to open now:
    # ensure_open()
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    i3 = i3ipc.Connection()             # sway-compatible
    i3.on("window::focus", on_window_focus)
    print("Haptics watcher: will auto-reopen Bolt HID++ (slot idx = %d)…" % DEVICE_IDX)
    try:
        i3.main()
    finally:
        cleanup()
