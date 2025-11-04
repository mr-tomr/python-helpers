# InterfacePresence.py
# Requirements (Windows):
#   pip install pyautogui pynput pywin32
#
# Features:
# - Human-like, non-constant cursor movement (curved paths + jitter + idle variance)
# - Timing variance for actions and typing cadence
# - Start/Stop from UI (and ESC as a global kill)
# - Click-to-target typing into an already-open window (no spawning)
# - Fully resizable window; grid-managed layout with sensible minimums
# - DPI-aware on Windows; UI scale slider for high-DPI screens
#
# Tips:
# - Move the mouse to a screen corner to trigger PyAutoGUI FAILSAFE if needed.

import threading
import random
import time
import tkinter as tk
from tkinter import ttk
import sys
import math

import pyautogui
from pynput import keyboard, mouse

# Windows helper imports (optional on non-Windows)
try:
    import ctypes
    import win32gui
    import win32con
    import win32api
except Exception:
    ctypes = None
    win32gui = None
    win32con = None
    win32api = None

pyautogui.FAILSAFE = True  # corner of screen triggers safety exception

# ------------------------------
# DPI awareness (Windows)
# ------------------------------
def _enable_dpi_awareness():
    if ctypes is None:
        return
    try:
        # Try Windows 10+ Per-Monitor V2 first
        shcore = ctypes.windll.shcore
        shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
        except Exception:
            pass

_enable_dpi_awareness()

# ------------------------------
# Random helpers (human cadence)
# ------------------------------
def r_between(a, b):
    return random.uniform(a, b)

def jitter(val, j=3.0):
    return val + random.uniform(-j, j)

def human_delay(base_min=0.08, base_max=0.22, occasional_pause_chance=0.07):
    d = r_between(base_min, base_max)
    if random.random() < occasional_pause_chance:
        d += r_between(0.3, 1.2)
    time.sleep(d)

def human_interval_for_char():
    # Gaussian-ish per-char delay
    return max(0.015, random.gauss(0.07, 0.03))

# ------------------------------
# Mouse pathing
# ------------------------------
def _bezier_points(p0, p1, ctrl, steps=30):
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl[0] + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl[1] + t ** 2 * p1[1]
        yield (x, y)

def move_mouse_human(to_x, to_y, duration=0.8):
    start_x, start_y = pyautogui.position()
    mid_x = (start_x + to_x) / 2 + random.uniform(-120, 120)
    mid_y = (start_y + to_y) / 2 + random.uniform(-120, 120)
    pts = list(_bezier_points((start_x, start_y), (to_x, to_y), (mid_x, mid_y), steps=30))
    seg_base = max(0.01, duration / len(pts))
    for (x, y) in pts:
        pyautogui.moveTo(jitter(x, 1.5), jitter(y, 1.5), duration=0)
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
    for ch in text:
        if ch == '\n':
            pyautogui.press('enter')
        else:
            pyautogui.typewrite(ch, interval=0)
        time.sleep(human_interval_for_char())
        if ch in ' .,;:!?':
            if random.random() < 0.20:
                time.sleep(random.uniform(0.15, 0.35))

# ------------------------------
# Window targeting (Windows focus)
# ------------------------------
def bring_window_to_front_at_point(pt):
    if win32gui is None or win32con is None:
        return True  # best-effort on non-Windows
    x, y = pt
    hwnd = win32gui.WindowFromPoint((int(x), int(y)))
    if not hwnd:
        return False
    hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False

# ------------------------------
# Worker thread: randomized activity
# ------------------------------
class PresenceThread(threading.Thread):
    def __init__(self, stop_evt, min_idle, max_idle):
        super().__init__(daemon=True)
        self.stop_evt = stop_evt
        self.min_idle = min_idle
        self.max_idle = max_idle

    def run(self):
        scr_w, scr_h = pyautogui.size()
        while not self.stop_evt.is_set():
            action = random.choices(
                population=["move_far", "jitter", "idle", "scroll_then_jitter"],
                weights=[0.35, 0.35, 0.15, 0.15],
                k=1
            )[0]

            if action == "move_far":
                target = (random.randint(40, scr_w - 40), random.randint(40, scr_h - 60))
                move_mouse_human(*target, duration=random.uniform(0.4, 1.4))
                human_delay(0.05, 0.25)

            elif action == "jitter":
                small_jitter_walk(steps=random.randint(6, 15))
                human_delay(0.08, 0.3)

            elif action == "scroll_then_jitter":
                occasional_scroll()
                small_jitter_walk(steps=random.randint(4, 10))

            # Idle with variance and occasional micro-movements
            idle_s = r_between(self.min_idle, self.max_idle)
            t0 = time.time()
            while time.time() - t0 < idle_s and not self.stop_evt.is_set():
                if random.random() < 0.08:
                    small_jitter_walk(steps=random.randint(2, 5))
                time.sleep(random.uniform(0.05, 0.2))

# ------------------------------
# App UI
# ------------------------------
class InterfacePresenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interface Presence")
        # Fully resizable; set sensible minimum size
        self.minsize(640, 400)

        # Theme
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("vista")
        except Exception:
            pass

        # UI Scale for high-DPI
        self.ui_scale = tk.DoubleVar(value=1.0)
        self.tk.call('tk', 'scaling', self.ui_scale.get())

        # Listener & worker state
        self.stop_evt = threading.Event()
        self.presence_thread = None
        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

        # Root grid config
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Main frame
        self.root_frame = ttk.Frame(self, padding=12)
        self.root_frame.grid(row=0, column=0, sticky="nsew")
        for c in range(12):
            self.root_frame.columnconfigure(c, weight=1)
        for r in range(20):
            self.root_frame.rowconfigure(r, weight=0)
        # Make the big text box expand
        self.root_frame.rowconfigure(9, weight=1)
        self.root_frame.rowconfigure(10, weight=1)

        r = 0
        header = ttk.Label(self.root_frame, text="Interface Presence", font=("Segoe UI", 14, "bold"))
        header.grid(row=r, column=0, columnspan=12, sticky="w")
        r += 1

        # Controls
        ttk.Label(self.root_frame, text="Idle (min s):").grid(row=r, column=0, sticky="e", padx=(0,6), pady=(8,0))
        self.min_idle = tk.DoubleVar(value=2.0)
        ttk.Spinbox(self.root_frame, from_=0.0, to=60.0, increment=0.5, textvariable=self.min_idle, width=8)\
            .grid(row=r, column=1, sticky="w", pady=(8,0))

        ttk.Label(self.root_frame, text="Idle (max s):").grid(row=r, column=2, sticky="e", padx=(12,6), pady=(8,0))
        self.max_idle = tk.DoubleVar(value=6.0)
        ttk.Spinbox(self.root_frame, from_=0.5, to=120.0, increment=0.5, textvariable=self.max_idle, width=8)\
            .grid(row=r, column=3, sticky="w", pady=(8,0))

        self.start_btn = ttk.Button(self.root_frame, text="Start", command=self.start_presence)
        self.stop_btn  = ttk.Button(self.root_frame, text="Stop",  command=self.stop_presence, state="disabled")
        self.start_btn.grid(row=r, column=5, sticky="w", padx=(18,6), pady=(8,0))
        self.stop_btn.grid(row=r, column=6, sticky="w", pady=(8,0))
        ttk.Label(self.root_frame, text="(ESC stops)").grid(row=r, column=7, sticky="w", pady=(8,0))
        r += 1

        # UI scale
        ttk.Label(self.root_frame, text="UI scale:").grid(row=r, column=0, sticky="e", padx=(0,6))
        scale = ttk.Scale(self.root_frame, from_=0.8, to=1.8, variable=self.ui_scale, command=self._on_scale_change)
        scale.grid(row=r, column=1, columnspan=3, sticky="ew")
        r += 1

        ttk.Separator(self.root_frame, orient="horizontal").grid(row=r, column=0, columnspan=12, sticky="ew", pady=10)
        r += 1

        # Typing section
        ttk.Label(self.root_frame, text="Click-to-Target Typing", font=("Segoe UI", 12, "bold"))\
            .grid(row=r, column=0, columnspan=6, sticky="w")
        r += 1

        ttk.Label(self.root_frame, text="After pressing the button, click inside the window you want to type into.")\
            .grid(row=r, column=0, columnspan=10, sticky="w")
        r += 1

        self.pick_and_type_btn = ttk.Button(self.root_frame, text="Pick target (next click) & Type", command=self.pick_and_type)
        self.pick_and_type_btn.grid(row=r, column=0, sticky="w")
        r += 1

        ttk.Label(self.root_frame, text="Text to type:").grid(row=r, column=0, sticky="nw", pady=(8,0))
        self.text_box = tk.Text(self.root_frame, height=10, wrap="word")
        self.text_box.grid(row=r, column=1, columnspan=10, sticky="nsew", padx=(6,0), pady=(8,0))
        self.text_box.insert("1.0", "This is a human-like typing demo.\nYou can paste any content here.")
        r += 1

        ttk.Separator(self.root_frame, orient="horizontal").grid(row=r, column=0, columnspan=12, sticky="ew", pady=10)
        r += 1

        self.status = tk.StringVar(value="Idle.")
        ttk.Label(self.root_frame, textvariable=self.status, foreground="#555").grid(row=r, column=0, columnspan=12, sticky="w")

        # Make text area expand with window
        self.root_frame.rowconfigure(r-2, weight=1)  # the text box row expands
        self.root_frame.columnconfigure(10, weight=3)

        # Bind closing to stop threads/listeners
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----- UI scaling -----
    def _on_scale_change(self, *_):
        try:
            self.tk.call('tk', 'scaling', float(self.ui_scale.get()))
        except Exception:
            pass

    # ----- Presence control -----
    def start_presence(self):
        if self.presence_thread and self.presence_thread.is_alive():
            return
        self.stop_evt.clear()
        mi = float(self.min_idle.get())
        ma = float(self.max_idle.get())
        if ma < mi:
            mi, ma = ma, mi
            self.min_idle.set(mi); self.max_idle.set(ma)
        self.presence_thread = PresenceThread(self.stop_evt, mi, ma)
        self.presence_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set("Presence simulation started.")

    def stop_presence(self):
        self.stop_evt.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Stopped.")

    # ----- Global keyboard safety -----
    def _on_key_press(self, key):
        try:
            if key == keyboard.Key.esc:
                self.stop_presence()
        except Exception:
            pass

    # ----- Click-to-target typing -----
    def pick_and_type(self):
        self.status.set("Waiting for your next click to choose target window...")
        self.update_idletasks()

        # Hide self to avoid selecting it
        self.withdraw()
        clicked = {}

        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                clicked['pt'] = (x, y)
                return False

        listener = mouse.Listener(on_click=on_click)
        listener.start()
        listener.join(timeout=30.0)
        self.deiconify()

        if 'pt' not in clicked:
            self.status.set("No click captured. Try again.")
            return

        ok = bring_window_to_front_at_point(clicked['pt'])
        time.sleep(0.15)
        if not ok:
            self.status.set("Could not focus target; typing into current focus.")
        else:
            self.status.set("Target focused. Typing...")

        text = self.text_box.get("1.0", "end-1c")
        try:
            type_text_human(text)
            self.status.set("Done typing.")
        except pyautogui.FailSafeException:
            self.status.set("Interrupted by PyAutoGUI FAILSAFE.")
        except Exception as e:
            self.status.set(f"Typing error: {e}")

    # ----- Clean shutdown -----
    def _on_close(self):
        try:
            self.stop_evt.set()
            if self.kb_listener:
                self.kb_listener.stop()
        except Exception:
            pass
        self.destroy()

# ------------------------------
# Entry
# ------------------------------
if __name__ == "__main__":
    try:
        app = InterfacePresenceApp()
        app.mainloop()
    except pyautogui.FailSafeException:
        print("PyAutoGUI FAILSAFE triggered.", file=sys.stderr)
    except KeyboardInterrupt:
        pass
