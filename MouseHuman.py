# MouseMover_Human.py
# Requirements (Windows):
#   pip install pyautogui pynput pywin32
#
# What you get:
# - Randomized, non-constant mouse movement with natural pauses and path jitter
# - Timing variance for all actions
# - GUI (Tkinter) with Start/Stop
# - Click-to-target typing: click the window you want to type into (no spawning)
# - ESC (global) abort via keyboard listener as a safety
#
# Notes:
# - On multi-monitor setups, pyautogui uses the virtual screen coordinates.
# - If SetForegroundWindow fails due to focus rules, a quick Alt press usually resolves it.

import threading
import random
import time
import math
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui
from pynput import keyboard, mouse

# Windows focus helpers
try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    win32gui = None

pyautogui.FAILSAFE = True  # Move mouse to a screen corner to raise FailSafeException

# ------------------------------
# Random helpers (human cadence)
# ------------------------------

def r_between(a, b):
    return random.uniform(a, b)

def jitter(val, j=3.0):
    return val + random.uniform(-j, j)

def human_delay(base_min=0.08, base_max=0.22, occasional_pause_chance=0.07):
    """
    Small per-action delay with a chance of a longer 'thinking' pause.
    """
    d = r_between(base_min, base_max)
    if random.random() < occasional_pause_chance:
        d += r_between(0.3, 1.2)
    time.sleep(d)

def human_interval_for_char():
    # Per-character variance (log-normal-ish feel without heavyweight math)
    return max(0.015, random.gauss(0.07, 0.03))

# ------------------------------
# Paths & movement
# ------------------------------

def bezier_points(p0, p1, ctrl, steps=30):
    for i in range(steps+1):
        t = i / steps
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * ctrl[0] + t**2 * p1[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * ctrl[1] + t**2 * p1[1]
        yield (x, y)

def move_mouse_human(to_x, to_y, duration=0.8):
    """
    Curved movement with slight jitter to avoid robotic lines.
    Duration is approximate; we pace by segment timing.
    """
    start_x, start_y = pyautogui.position()
    # Mid control point somewhere off the straight line
    mid_x = (start_x + to_x) / 2 + random.uniform(-120, 120)
    mid_y = (start_y + to_y) / 2 + random.uniform(-120, 120)
    pts = list(bezier_points((start_x, start_y), (to_x, to_y), (mid_x, mid_y), steps=30))
    # Total time split across segments with variance
    seg_base = max(0.01, duration / len(pts))
    for (x, y) in pts:
        pyautogui.moveTo(jitter(x, 1.5), jitter(y, 1.5), duration=0)  # we control timing manually
        time.sleep(seg_base * random.uniform(0.6, 1.4))

def small_jitter_walk(steps=10):
    for _ in range(steps):
        x, y = pyautogui.position()
        dx = random.randint(-5, 5)
        dy = random.randint(-4, 6)
        pyautogui.moveTo(x + dx, y + dy, duration=0)
        time.sleep(random.uniform(0.01, 0.06))

def occasional_scroll():
    if random.random() < 0.25:
        amount = random.choice([1, 2, -1, -2, 3, -3]) * random.randint(20, 60)
        pyautogui.scroll(amount)
        human_delay(0.1, 0.25, occasional_pause_chance=0)

# ------------------------------
# Typing
# ------------------------------

def type_text_human(text):
    """
    Types the provided text into the focused window with human-like variance.
    Supports \n in the text.
    """
    for ch in text:
        if ch == '\n':
            pyautogui.press('enter')
        else:
            pyautogui.typewrite(ch, interval=0)  # we control timing below
        time.sleep(human_interval_for_char())
        # rare micro-pause between words/punctuation
        if ch in ' .,;:!?':
            if random.random() < 0.20:
                time.sleep(random.uniform(0.15, 0.35))

# ------------------------------
# Window targeting
# ------------------------------

def bring_window_to_front_at_point(pt):
    """
    Given a screen point (x, y), get the window there and bring to foreground.
    Returns True if successful.
    """
    if win32gui is None:
        return True  # best effort on non-Windows – rely on focus already being correct

    x, y = pt
    hwnd = win32gui.WindowFromPoint((int(x), int(y)))
    if not hwnd:
        return False

    # If it's a child, climb to top-level
    hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
    try:
        # Restore if minimized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # Bring to foreground
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False

# ------------------------------
# Worker thread: randomized activity
# ------------------------------

class MoverThread(threading.Thread):
    def __init__(self, stop_evt, min_idle, max_idle):
        super().__init__(daemon=True)
        self.stop_evt = stop_evt
        self.min_idle = min_idle
        self.max_idle = max_idle

    def run(self):
        scr_w, scr_h = pyautogui.size()
        while not self.stop_evt.is_set():
            # Randomly pick an action
            action = random.choices(
                population=["move_far", "jitter", "idle", "scroll_then_jitter"],
                weights=[0.35, 0.35, 0.15, 0.15],
                k=1
            )[0]

            if action == "move_far":
                # Go to a random region, with a curved path
                target = (random.randint(40, scr_w - 40), random.randint(40, scr_h - 60))
                move_mouse_human(*target, duration=random.uniform(0.4, 1.4))
                human_delay(0.05, 0.25)

            elif action == "jitter":
                small_jitter_walk(steps=random.randint(6, 15))
                human_delay(0.08, 0.3)

            elif action == "scroll_then_jitter":
                occasional_scroll()
                small_jitter_walk(steps=random.randint(4, 10))

            # Idle with variance (natural “thinking”)
            idle_s = r_between(self.min_idle, self.max_idle)
            # A little brownian micro-movement during idle sometimes
            t0 = time.time()
            while time.time() - t0 < idle_s and not self.stop_evt.is_set():
                if random.random() < 0.08:
                    small_jitter_walk(steps=random.randint(2, 5))
                time.sleep(random.uniform(0.05, 0.2))

# ------------------------------
# Tkinter UI
# ------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Human Mouse & Typing")
        self.geometry("540x320")
        self.resizable(False, False)

        self.stop_evt = threading.Event()
        self.mover_thread = None

        # Keyboard safety: ESC stops
        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

        # UI
        f = ttk.Frame(self, padding=12)
        f.pack(fill="both", expand=True)

        row = 0
        ttk.Label(f, text="Randomized Mouse Activity", font=("Segoe UI", 12, "bold")).grid(column=0, row=row, sticky="w", columnspan=4)
        row += 1

        ttk.Label(f, text="Idle (min s):").grid(column=0, row=row, sticky="e")
        self.min_idle = tk.DoubleVar(value=2.0)
        ttk.Spinbox(f, from_=0.0, to=60.0, increment=0.5, textvariable=self.min_idle, width=6).grid(column=1, row=row, sticky="w", padx=(6, 18))

        ttk.Label(f, text="Idle (max s):").grid(column=2, row=row, sticky="e")
        self.max_idle = tk.DoubleVar(value=6.0)
        ttk.Spinbox(f, from_=0.5, to=120.0, increment=0.5, textvariable=self.max_idle, width=6).grid(column=3, row=row, sticky="w")
        row += 1

        self.start_btn = ttk.Button(f, text="Start", command=self.start)
        self.stop_btn  = ttk.Button(f, text="Stop",  command=self.stop, state="disabled")
        self.start_btn.grid(column=0, row=row, pady=(8, 10), sticky="w")
        self.stop_btn.grid(column=1, row=row, pady=(8, 10), sticky="w")
        ttk.Label(f, text="(ESC also stops)").grid(column=2, row=row, sticky="w")
        row += 1

        ttk.Separator(f, orient='horizontal').grid(column=0, row=row, columnspan=4, sticky="ew", pady=10)
        row += 1

        ttk.Label(f, text="Click-to-Target Typing", font=("Segoe UI", 12, "bold")).grid(column=0, row=row, sticky="w", columnspan=4)
        row += 1

        ttk.Label(f, text="Text to type:").grid(column=0, row=row, sticky="ne", pady=(2, 0))
        self.text_box = tk.Text(f, height=6, width=48, wrap="word")
        self.text_box.grid(column=1, row=row, columnspan=3, sticky="w", padx=(6,0))
        self.text_box.insert("1.0", "This is a human-like typing demo.\nYou can paste any content here.")

        row += 1
        row += 1

        self.pick_and_type_btn = ttk.Button(f, text="Pick target (next click) & Type", command=self.pick_and_type)
        self.pick_and_type_btn.grid(column=0, row=row, pady=(6,0), sticky="w")

        ttk.Label(f, text="After clicking this button, click inside the window you want to type into (e.g., Notepad).").grid(column=1, row=row, columnspan=3, sticky="w", padx=(10,0))
        row += 1

        self.status = tk.StringVar(value="Idle.")
        ttk.Label(f, textvariable=self.status, foreground="#555").grid(column=0, row=row, columnspan=4, sticky="w", pady=(10,0))

        for c in range(4):
            f.grid_columnconfigure(c, weight=1)

    # ---- Movement control ----
    def start(self):
        if self.mover_thread and self.mover_thread.is_alive():
            return
        self.stop_evt.clear()
        mi = float(self.min_idle.get())
        ma = float(self.max_idle.get())
        if ma < mi:
            mi, ma = ma, mi
            self.min_idle.set(mi); self.max_idle.set(ma)
        self.mover_thread = MoverThread(self.stop_evt, mi, ma)
        self.mover_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set("Mouse activity started.")

    def stop(self):
        self.stop_evt.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Stopped.")

    def _on_key_press(self, key):
        # ESC global stop
        try:
            if key == keyboard.Key.esc:
                self.stop()
        except Exception:
            pass

    # ---- Click-to-target typing ----
    def pick_and_type(self):
        self.status.set("Waiting for your next click to choose target window...")
        self.update_idletasks()

        # Temporarily hide the app window to avoid selecting itself
        self.withdraw()
        clicked = {}

        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                clicked['pt'] = (x, y)
                return False  # stop listener

        listener = mouse.Listener(on_click=on_click)
        listener.start()
        listener.join(timeout=30.0)

        self.deiconify()

        if 'pt' not in clicked:
            self.status.set("No click captured. Try again.")
            return

        # Focus the window under the click
        ok = bring_window_to_front_at_point(clicked['pt'])
        time.sleep(0.15)
        if not ok:
            self.status.set("Could not focus target window; typing anyway into current focus.")
        else:
            self.status.set("Target focused. Typing...")

        # Type with variance
        text = self.text_box.get("1.0", "end-1c")
        try:
            type_text_human(text)
            self.status.set("Done typing.")
        except pyautogui.FailSafeException:
            self.status.set("Typing interrupted by PyAutoGUI FAILSAFE (mouse hit a screen corner).")
        except Exception as e:
            self.status.set(f"Typing error: {e}")

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except pyautogui.FailSafeException:
        print("PyAutoGUI FAILSAFE triggered.", file=sys.stderr)
