# InterfacePresence.py
# Purpose: keep a session active by emulating human presence with a mix of
#          small "micro" movements and meaningful cross-screen moves.
# - Human easing (accelerate → coast → decelerate) + tiny jitter
# - Occasional overshoot + correction to feel natural
# - Brief dwells, optional rare clicks & scrolls (configurable)
# - Start/Stop, ESC to stop, DPI-aware UI with zoom, resizable window
# - Optional "click-to-target typing" tool for demos (does nothing unless used)

import threading
import random
import time
import sys
import math
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

import pyautogui
from pynput import keyboard, mouse

# Optional Windows helpers (focus + DPI)
try:
    import ctypes
    import win32gui
    import win32con
except Exception:
    ctypes = None
    win32gui = None
    win32con = None

pyautogui.FAILSAFE = True  # fling cursor to a corner to abort any pyautogui action

# -------------------- DPI helpers --------------------
def _enable_dpi_awareness_windows():
    if ctypes is None:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor V2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def _get_system_dpi_windows():
    if ctypes is None:
        return None
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        return int(dpi)
    except Exception:
        pass
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return int(dpi)
    except Exception:
        pass
    return None

def _default_tk_scaling():
    _enable_dpi_awareness_windows()
    dpi = _get_system_dpi_windows()
    if dpi:
        return max(1.1, round(dpi / 72.0, 2))  # tk expects pixels/point (1 pt = 1/72")
    return 1.33

# -------------------- randomness helpers --------------------
def _r(a, b): return random.uniform(a, b)
def _ri(a, b): return random.randint(a, b)
def _j(v, j=1.4): return v + random.uniform(-j, j)

# -------------------- easing & paths --------------------
def _ease_in_out_cubic(t: float) -> float:
    return 4*t*t*t if t < 0.5 else 1 - pow(-2*t + 2, 3) / 2

def _bezier(p0, p1, c, steps=48):
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * c[0] + t**2 * p1[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * c[1] + t**2 * p1[1]
        yield (x, y), t

def _human_move_path(sx, sy, tx, ty, steps=48, overshoot_prob=0.25):
    # Single control point with offset → gentle curve
    cx = (sx + tx) / 2 + _r(-120, 120)
    cy = (sy + ty) / 2 + _r(-120, 120)

    # Optionally overshoot a little then correct back
    overshoot = (random.random() < overshoot_prob)
    if overshoot:
        ox = tx + _r(-35, 35)
        oy = ty + _r(-35, 35)
        # path 1: to near target but pass it a bit
        pts1 = list(_bezier((sx, sy), (ox, oy), (cx, cy), steps=max(24, steps//2)))
        # small pause, then correction micro-path
        cx2 = (ox + tx) / 2 + _r(-40, 40)
        cy2 = (oy + ty) / 2 + _r(-40, 40)
        pts2 = list(_bezier((ox, oy), (tx, ty), (cx2, cy2), steps=max(18, steps//3)))
        return pts1 + pts2
    else:
        return list(_bezier((sx, sy), (tx, ty), (cx, cy), steps=steps))

def _sleep_deltas_for_duration(duration, n_steps):
    # Allocate time per step using easing so motion accelerates then slows
    eased = [_ease_in_out_cubic(i / n_steps) for i in range(n_steps + 1)]
    total = eased[-1] - eased[0]
    if total <= 0:
        total = 1.0
    times = [duration * (e - eased[0]) / total for e in eased]
    deltas = [max(0.002, times[i+1] - times[i]) for i in range(n_steps)]
    return deltas

def move_mouse_human(tx, ty, duration=0.6, steps=44):
    sx, sy = pyautogui.position()
    pts = _human_move_path(sx, sy, tx, ty, steps=steps, overshoot_prob=0.28)
    sleeps = _sleep_deltas_for_duration(duration, len(pts) - 1)
    # Walk the path with tiny jitter and slight timing variance
    for ((x, y), _t), slp in zip(pts[1:], sleeps):
        pyautogui.moveTo(_j(x), _j(y), duration=0)
        time.sleep(slp * _r(0.90, 1.12))

def micro_jitter(steps=10):
    for _ in range(steps):
        x, y = pyautogui.position()
        pyautogui.moveTo(x + _ri(-5, 5), y + _ri(-4, 6), duration=0)
        time.sleep(_r(0.01, 0.05))

def occasional_scroll():
    amt = random.choice([1, 2, -1, -2, 3, -3]) * _ri(20, 60)
    pyautogui.scroll(amt)

# -------------------- typing tool (optional) --------------------
def _char_interval(): return max(0.015, random.gauss(0.07, 0.03))
def type_text_human(text):
    for ch in text:
        if ch == '\n': pyautogui.press('enter')
        else: pyautogui.typewrite(ch, interval=0)
        time.sleep(_char_interval())

# -------------------- focus helper --------------------
def bring_window_to_front_at_point(pt):
    if win32gui is None or win32con is None:
        return True
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

# -------------------- behavior mixer --------------------
class PresenceThread(threading.Thread):
    """
    Blends micro movements with meaningful cross-screen moves:
      - micro: small jitter clusters that run frequently
      - meaningful: decisive move to a far region with eased speed and occasional overshoot+correction
      - brief dwells with tiny nudges so system idle never builds up
    Optional: rare click / rare scroll.
    """
    def __init__(self, stop_evt, min_idle, max_idle,
                 micro_weight, meaningful_weight,
                 click_enabled, scroll_enabled,
                 click_prob, scroll_prob,
                 screen_margin):
        super().__init__(daemon=True)
        self.stop_evt = stop_evt
        self.min_idle = min_idle
        self.max_idle = max_idle
        self.micro_weight = micro_weight
        self.meaningful_weight = meaningful_weight
        self.click_enabled = click_enabled
        self.scroll_enabled = scroll_enabled
        self.click_prob = click_prob
        self.scroll_prob = scroll_prob
        self.screen_margin = screen_margin

    def _maybe_click(self):
        if self.click_enabled and random.random() < self.click_prob:
            pyautogui.click()
            time.sleep(_r(0.08, 0.22))

    def _maybe_scroll(self):
        if self.scroll_enabled and random.random() < self.scroll_prob:
            occasional_scroll()
            time.sleep(_r(0.08, 0.25))

    def _rand_screen_point(self):
        sw, sh = pyautogui.size()
        m = self.screen_margin
        return _ri(m, sw - m), _ri(m, sh - m)

    def _meaningful_move(self):
        # choose a point across the screen, biased away from current spot
        cx, cy = pyautogui.position()
        sw, sh = pyautogui.size()
        m = self.screen_margin
        # Prefer farther targets: try multiple and pick the farthest
        candidates = [self._rand_screen_point() for _ in range(5)]
        tx, ty = max(candidates, key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
        # Duration scales with distance so it doesn't "teleport"
        dist = math.hypot(tx - cx, ty - cy)
        base = 0.35 + min(1.4, dist / max(sw, sh))  # 0.35..~1.75
        move_mouse_human(tx, ty, duration=base * _r(0.9, 1.1), steps=_ri(36, 54))
        # brief dwell & micro-correct (humans wiggle a bit after landing)
        time.sleep(_r(0.05, 0.18))
        if random.random() < 0.65:
            micro_jitter(_ri(3, 8))

    def _micro_move(self):
        # tight cluster of small changes; occasionally include a mini hop
        micro_jitter(_ri(7, 16))
        if random.random() < 0.25:
            x, y = pyautogui.position()
            pyautogui.moveTo(x + _ri(-15, 15), y + _ri(-12, 18), duration=0)
            time.sleep(_r(0.02, 0.06))

    def run(self):
        while not self.stop_evt.is_set():
            # choose action weighted by user sliders
            action = random.choices(
                ["micro", "meaningful", "scroll", "idle"],
                weights=[self.micro_weight, self.meaningful_weight, 0.07, 0.13],
                k=1
            )[0]

            if action == "micro":
                self._micro_move()
                self._maybe_click()

            elif action == "meaningful":
                self._meaningful_move()
                self._maybe_click()

            elif action == "scroll":
                self._maybe_scroll()
                self._micro_move()

            # Idle with periodic tiny nudges so OS never counts true idle
            idle_for = _r(self.min_idle, self.max_idle)
            t0 = time.time()
            while time.time() - t0 < idle_for and not self.stop_evt.is_set():
                if random.random() < 0.22:  # nudge during idle
                    self._micro_move()
                    self._maybe_click()
                time.sleep(_r(0.25, 0.8))

# -------------------- UI --------------------
class InterfacePresenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interface Presence")

        # DPI + fonts
        self._base_scaling = _default_tk_scaling()
        self._zoom = tk.DoubleVar(value=self._base_scaling)
        self.tk.call('tk', 'scaling', self._zoom.get())

        tkfont.nametofont("TkDefaultFont").configure(size=12)
        tkfont.nametofont("TkTextFont").configure(size=12)
        tkfont.nametofont("TkHeadingFont").configure(size=15, weight="bold")
        tkfont.nametofont("TkMenuFont").configure(size=12)

        self.minsize(880, 560)
        self.style = ttk.Style(self)
        try: self.style.theme_use("vista")
        except Exception: pass

        # State
        self.stop_evt = threading.Event()
        self.presence_thread = None
        self.kb_listener = keyboard.Listener(on_press=self._on_key)
        self.kb_listener.start()

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_menu()
        self._build_main()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----- Menu / Zoom -----
    def _build_menu(self):
        menubar = tk.Menu(self)
        view = tk.Menu(menubar, tearoff=False)
        view.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view.add_command(label="Reset Zoom", command=self.zoom_reset, accelerator="Ctrl+0")
        menubar.add_cascade(label="View", menu=view)
        self.config(menu=menubar)

        self.bind_all("<Control-plus>", lambda e: self.zoom_in())
        self.bind_all("<Control-KP_Add>", lambda e: self.zoom_in())
        self.bind_all("<Control-minus>", lambda e: self.zoom_out())
        self.bind_all("<Control-KP_Subtract>", lambda e: self.zoom_out())
        self.bind_all("<Control-0>", lambda e: self.zoom_reset())

    def zoom_in(self):  self._set_zoom(self._zoom.get() + 0.1)
    def zoom_out(self): self._set_zoom(self._zoom.get() - 0.1)
    def zoom_reset(self): self._set_zoom(self._base_scaling)
    def _set_zoom(self, val):
        self._zoom.set(max(0.8, min(3.0, round(val, 2))))
        self.tk.call('tk', 'scaling', self._zoom.get())
        self.update_idletasks()

    # ----- Main -----
    def _build_main(self):
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        for c in range(12): root.columnconfigure(c, weight=1)
        for r in range(30): root.rowconfigure(r, weight=0)

        r = 0
        ttk.Label(root, text="Interface Presence", font=("TkHeadingFont")).grid(row=r, column=0, columnspan=12, sticky="w")
        r += 1
        ttk.Separator(root, orient="horizontal").grid(row=r, column=0, columnspan=12, sticky="ew", pady=(6, 10))
        r += 1

        # Timing sliders
        ttk.Label(root, text="Idle (min s):").grid(row=r, column=0, sticky="e")
        self.min_idle = tk.DoubleVar(value=1.3)
        ttk.Spinbox(root, from_=0.0, to=60.0, increment=0.5, textvariable=self.min_idle, width=7).grid(row=r, column=1, sticky="w")

        ttk.Label(root, text="Idle (max s):").grid(row=r, column=2, sticky="e")
        self.max_idle = tk.DoubleVar(value=3.6)
        ttk.Spinbox(root, from_=0.5, to=120.0, increment=0.5, textvariable=self.max_idle, width=7).grid(row=r, column=3, sticky="w")

        # Movement mix (micro vs meaningful)
        ttk.Label(root, text="Micro weight:").grid(row=r, column=5, sticky="e")
        self.micro_weight = tk.DoubleVar(value=0.58)
        ttk.Spinbox(root, from_=0.0, to=1.0, increment=0.01, textvariable=self.micro_weight, width=6).grid(row=r, column=6, sticky="w")

        ttk.Label(root, text="Meaningful weight:").grid(row=r, column=7, sticky="e")
        self.meaningful_weight = tk.DoubleVar(value=0.32)
        ttk.Spinbox(root, from_=0.0, to=1.0, increment=0.01, textvariable=self.meaningful_weight, width=6).grid(row=r, column=8, sticky="w")

        self.start_btn = ttk.Button(root, text="Start", command=self.start_presence)
        self.stop_btn  = ttk.Button(root, text="Stop",  command=self.stop_presence, state="disabled")
        self.start_btn.grid(row=r, column=10, sticky="w")
        self.stop_btn.grid(row=r, column=11, sticky="w")
        r += 1

        # Behavior toggles
        self.click_enabled = tk.BooleanVar(value=True)
        self.scroll_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(root, text="Occasional click", variable=self.click_enabled).grid(row=r, column=0, sticky="w")
        ttk.Checkbutton(root, text="Occasional scroll", variable=self.scroll_enabled).grid(row=r, column=1, sticky="w")

        ttk.Label(root, text="Click prob:").grid(row=r, column=2, sticky="e")
        self.click_prob = tk.DoubleVar(value=0.03)
        ttk.Spinbox(root, from_=0.0, to=0.2, increment=0.005, textvariable=self.click_prob, width=6).grid(row=r, column=3, sticky="w")

        ttk.Label(root, text="Scroll prob:").grid(row=r, column=4, sticky="e")
        self.scroll_prob = tk.DoubleVar(value=0.07)
        ttk.Spinbox(root, from_=0.0, to=0.3, increment=0.01, textvariable=self.scroll_prob, width=6).grid(row=r, column=5, sticky="w")

        ttk.Label(root, text="Screen margin (px):").grid(row=r, column=7, sticky="e")
        self.screen_margin = tk.IntVar(value=60)
        ttk.Spinbox(root, from_=0, to=200, increment=5, textvariable=self.screen_margin, width=6).grid(row=r, column=8, sticky="w")
        r += 1

        # Zoom slider
        ttk.Label(root, text="Zoom:").grid(row=r, column=0, sticky="e")
        ttk.Scale(root, from_=0.8, to=3.0, variable=self._zoom, command=lambda *_: self._set_zoom(self._zoom.get())).grid(row=r, column=1, columnspan=3, sticky="ew")
        r += 1

        ttk.Separator(root, orient="horizontal").grid(row=r, column=0, columnspan=12, sticky="ew", pady=10)
        r += 1

        # Typing tool (optional)
        ttk.Label(root, text="Click-to-Target Typing (optional)", font=("TkHeadingFont")).grid(row=r, column=0, columnspan=6, sticky="w")
        r += 1
        ttk.Label(root, text="Press the button, then click inside the window you want to type into.").grid(row=r, column=0, columnspan=10, sticky="w")
        r += 1
        self.pick_btn = ttk.Button(root, text="Pick target (next click) & Type", command=self.pick_and_type)
        self.pick_btn.grid(row=r, column=0, sticky="w")
        r += 1

        ttk.Label(root, text="Text to type:").grid(row=r, column=0, sticky="nw")
        root.rowconfigure(r+1, weight=1)
        self.text_box = tk.Text(root, height=10)
        self.text_box.grid(row=r, column=1, columnspan=10, sticky="nsew", padx=(6, 0))
        self.text_box.insert("1.0", "This is a demo of human-like typing.\nIt only runs if you press the button above.")
        r += 2

        ttk.Separator(root, orient="horizontal").grid(row=r, column=0, columnspan=12, sticky="ew", pady=10)
        r += 1

        self.status = tk.StringVar(value="Idle.")
        ttk.Label(root, textvariable=self.status, foreground="#555").grid(row=r, column=0, columnspan=12, sticky="w")

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

        # normalize weights a bit so you can freely set sliders
        micro_w = float(self.micro_weight.get())
        meaningful_w = float(self.meaningful_weight.get())
        total = max(0.01, micro_w + meaningful_w)
        micro_w /= total
        meaningful_w /= total

        self.presence_thread = PresenceThread(
            self.stop_evt,
            mi, ma,
            micro_w, meaningful_w,
            self.click_enabled.get(),
            self.scroll_enabled.get(),
            float(self.click_prob.get()),
            float(self.scroll_prob.get()),
            int(self.screen_margin.get())
        )
        self.presence_thread.start()
        self.status.set("Presence running (mixed micro + meaningful movements).")
        self._toggle_buttons(True)

    def stop_presence(self):
        self.stop_evt.set()
        self.status.set("Stopped.")
        self._toggle_buttons(False)

    def _toggle_buttons(self, running):
        self.start_btn.config(state="disabled" if running else "normal")
        self.stop_btn.config(state="normal" if running else "disabled")

    # ----- Typing tool -----
    def pick_and_type(self):
        self.status.set("Waiting for your click to choose target window…")
        self.update_idletasks()
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
            self.status.set("No click captured.")
            return

        bring_window_to_front_at_point(clicked['pt'])
        time.sleep(0.15)
        self.status.set("Typing…")
        try:
            type_text_human(self.text_box.get("1.0", "end-1c"))
            self.status.set("Done typing.")
        except pyautogui.FailSafeException:
            self.status.set("Typing interrupted (FAILSAFE).")
        except Exception as e:
            self.status.set(f"Typing error: {e}")

    # ----- Global ESC -----
    def _on_key(self, key):
        if key == keyboard.Key.esc:
            self.stop_presence()

    # ----- Window close -----
    def _on_close(self):
        try:
            self.stop_evt.set()
            if hasattr(self, "kb_listener") and self.kb_listener:
                self.kb_listener.stop()
        except Exception:
            pass
        self.destroy()

# -------------------- main --------------------
if __name__ == "__main__":
    try:
        app = InterfacePresenceApp()
        app.mainloop()
    except pyautogui.FailSafeException:
        print("PyAutoGUI FAILSAFE triggered.", file=sys.stderr)
    except KeyboardInterrupt:
        pass
