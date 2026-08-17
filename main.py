#!/usr/bin/env python3
"""
Slideshow Presenter
--------------------
A lightweight photo slideshow app. Pick multiple folders, it recursively
finds every image inside them, shuffles them, and plays a fullscreen
slideshow with simple playback controls.

Standard library + Pillow only (no heavyweight frameworks).
"""

import json
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    print("Pillow is required. Install it with: pip3 install pillow")
    sys.exit(1)

APP_NAME = "Slideshow Presenter"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "slideshow-presenter")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}

DEFAULT_INTERVAL = 5  # seconds
CONTROLS_HIDE_DELAY_MS = 2500


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("folders", [])
            data.setdefault("interval", DEFAULT_INTERVAL)
            data.setdefault("show_captions", True)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"folders": [], "interval": DEFAULT_INTERVAL, "show_captions": True}


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def scan_images(folders):
    """Recursively collect image file paths from the given folders."""
    images = []
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for root, _dirs, files in os.walk(folder):
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    images.append(os.path.join(root, name))
    return images


class SetupWindow:
    """The launcher window: manage folders, set interval/captions, start."""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("560x420")
        self.root.minsize(480, 360)

        self.config = load_config()

        main = ttk.Frame(root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text=APP_NAME, font=("TkDefaultFont", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Add one or more folders, then start the slideshow. Images are shuffled and shown fullscreen.",
            wraplength=520,
        )
        subtitle.pack(anchor="w", pady=(2, 12))

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        for folder in self.config["folders"]:
            self.listbox.insert(tk.END, folder)

        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=(8, 12))

        ttk.Button(btn_row, text="Add Folder…", command=self.add_folder).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=(8, 0))

        options = ttk.Frame(main)
        options.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(options, text="Interval (seconds):").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.config.get("interval", DEFAULT_INTERVAL)))
        interval_spin = ttk.Spinbox(
            options, from_=1, to=3600, width=6, textvariable=self.interval_var
        )
        interval_spin.pack(side=tk.LEFT, padx=(6, 20))

        self.captions_var = tk.BooleanVar(value=self.config.get("show_captions", True))
        ttk.Checkbutton(
            options, text="Show filename / folder captions", variable=self.captions_var
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.status_var, foreground="#666").pack(anchor="w")

        start_row = ttk.Frame(main)
        start_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(start_row, text="Start Slideshow", command=self.start_slideshow).pack(
            side=tk.RIGHT
        )

        self._update_status()

    def _folders(self):
        return list(self.listbox.get(0, tk.END))

    def _update_status(self):
        n = len(self._folders())
        self.status_var.set(f"{n} folder(s) selected." if n else "No folders added yet.")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder with pictures")
        if folder and folder not in self._folders():
            self.listbox.insert(tk.END, folder)
        self._update_status()

    def remove_selected(self):
        for index in reversed(self.listbox.curselection()):
            self.listbox.delete(index)
        self._update_status()

    def _persist_config(self):
        try:
            interval = max(1, int(float(self.interval_var.get())))
        except ValueError:
            interval = DEFAULT_INTERVAL
        self.config["folders"] = self._folders()
        self.config["interval"] = interval
        self.config["show_captions"] = bool(self.captions_var.get())
        save_config(self.config)
        return interval

    def start_slideshow(self):
        folders = self._folders()
        if not folders:
            messagebox.showwarning(APP_NAME, "Add at least one folder first.")
            return

        interval = self._persist_config()

        self.status_var.set("Scanning folders for images…")
        self.root.update_idletasks()

        images = scan_images(folders)
        if not images:
            messagebox.showwarning(
                APP_NAME, "No supported image files were found in the selected folders."
            )
            self._update_status()
            return

        random.shuffle(images)
        self.root.withdraw()
        SlideshowWindow(
            self.root,
            images,
            interval=interval,
            show_captions=self.captions_var.get(),
            on_close=self._on_slideshow_close,
        )

    def _on_slideshow_close(self):
        self.root.deiconify()
        self._update_status()


class SlideshowWindow:
    """Fullscreen slideshow with playback controls and auto-hiding overlay."""

    def __init__(self, parent, images, interval, show_captions, on_close):
        self.parent = parent
        self.images = images
        self.index = 0
        self.interval = interval
        self.show_captions = show_captions
        self.on_close = on_close
        self.playing = True
        self._after_id = None
        self._hide_controls_id = None
        self._tk_image = None  # keep a reference so it isn't garbage-collected
        self._next_cache = {}  # index -> PIL Image, simple 1-ahead prefetch
        self._prefetch_lock = threading.Lock()

        self.win = tk.Toplevel(parent)
        self.win.title(APP_NAME)
        self.win.configure(bg="black")

        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        # Set an explicit full-screen geometry *before* requesting the
        # -fullscreen attribute. Some window managers apply -fullscreen
        # asynchronously (or not at all under unusual/minimal WMs), which
        # otherwise leaves the window at Tk's small default size and any
        # image rendered at that size looks like it vanished on a black
        # background. Forcing geometry first makes this reliable everywhere.
        self.win.geometry(f"{screen_w}x{screen_h}+0+0")
        self.win.update_idletasks()
        try:
            self.win.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        self.win.update_idletasks()
        self.win.update()
        self.win.focus_force()

        self.canvas = tk.Canvas(self.win, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_item = self.canvas.create_image(0, 0, anchor=tk.CENTER)

        self.caption_var = tk.StringVar()
        self.caption_label = tk.Label(
            self.win,
            textvariable=self.caption_var,
            bg="black",
            fg="white",
            font=("TkDefaultFont", 11),
            anchor="w",
        )

        # Controls overlay (auto-hides after inactivity)
        self.controls = tk.Frame(self.win, bg="#111111")
        self._build_controls()

        self.win.bind("<Escape>", lambda e: self.close())
        self.win.bind("<space>", lambda e: self.toggle_play())
        self.win.bind("<Right>", lambda e: self.next_image(manual=True))
        self.win.bind("<Left>", lambda e: self.prev_image(manual=True))
        self.win.bind("<Motion>", self._on_activity)
        self.win.bind("<Configure>", self._on_resize)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

        self._resize_job = None
        self._show_current(initial=True)
        self._schedule_hide_controls()
        self._schedule_advance()

    def _build_controls(self):
        for child in self.controls.winfo_children():
            child.destroy()

        btn_opts = dict(bg="#111111", fg="white", activebackground="#333333",
                         activeforeground="white", bd=0, padx=10, pady=6,
                         font=("TkDefaultFont", 11))

        tk.Button(self.controls, text="⏮ Prev", command=lambda: self.prev_image(manual=True), **btn_opts).pack(side=tk.LEFT)
        self.play_btn = tk.Button(self.controls, text="⏸ Pause", command=self.toggle_play, **btn_opts)
        self.play_btn.pack(side=tk.LEFT)
        tk.Button(self.controls, text="Next ⏭", command=lambda: self.next_image(manual=True), **btn_opts).pack(side=tk.LEFT)

        tk.Label(self.controls, text="Interval:", bg="#111111", fg="white",
                 font=("TkDefaultFont", 11)).pack(side=tk.LEFT, padx=(20, 4))
        tk.Button(self.controls, text="−", command=lambda: self.adjust_interval(-1), **btn_opts).pack(side=tk.LEFT)
        self.interval_label = tk.Label(self.controls, text=f"{self.interval}s", bg="#111111",
                                        fg="white", width=4, font=("TkDefaultFont", 11))
        self.interval_label.pack(side=tk.LEFT)
        tk.Button(self.controls, text="+", command=lambda: self.adjust_interval(1), **btn_opts).pack(side=tk.LEFT)

        self.counter_label = tk.Label(self.controls, bg="#111111", fg="#aaaaaa",
                                       font=("TkDefaultFont", 10))
        self.counter_label.pack(side=tk.LEFT, padx=(20, 0))

        tk.Button(self.controls, text="Exit (Esc)", command=self.close, **btn_opts).pack(side=tk.RIGHT)

    # -- image display -----------------------------------------------------

    def _load_display_image(self, path):
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        return img

    def _fit_and_render(self, pil_img):
        self.win.update_idletasks()
        win_w = self.win.winfo_width()
        win_h = self.win.winfo_height()
        # Guard against a not-yet-realized/mis-sized window (seen on some
        # window managers) by falling back to the actual screen size.
        if win_w <= 10 or win_h <= 10:
            win_w = self.win.winfo_screenwidth()
            win_h = self.win.winfo_screenheight()
        img_copy = pil_img.copy()
        img_copy.thumbnail((win_w, win_h), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(img_copy)
        self.canvas.coords(self.image_item, win_w // 2, win_h // 2)
        self.canvas.itemconfig(self.image_item, image=self._tk_image)

    def _show_current(self, initial=False):
        if not self.images:
            return
        path = self.images[self.index]
        try:
            cached = self._next_cache.pop(self.index, None)
            pil_img = cached if cached is not None else self._load_display_image(path)
        except Exception as exc:
            # Skip unreadable/corrupt files, but log it so it's diagnosable
            # when run from a terminal instead of just silently vanishing.
            print(f"[slideshow-presenter] could not read '{path}': {exc}", file=sys.stderr)
            self._remove_current_and_advance()
            return

        self._current_pil = pil_img
        self._fit_and_render(pil_img)

        if self.show_captions:
            folder = os.path.basename(os.path.dirname(path)) or path
            self.caption_var.set(f"{os.path.basename(path)}   —   {folder}")
            self.caption_label.place(relx=0, rely=1.0, anchor="sw", x=12, y=-8)
        else:
            self.caption_label.place_forget()

        self.counter_label.config(text=f"{self.index + 1} / {len(self.images)}")
        self._prefetch_next()

    def _remove_current_and_advance(self):
        if 0 <= self.index < len(self.images):
            del self.images[self.index]
        if not self.images:
            messagebox.showinfo(APP_NAME, "No more readable images.")
            self.close()
            return
        if self.index >= len(self.images):
            self.index = 0
        self._show_current()

    def _prefetch_next(self):
        nxt = (self.index + 1) % len(self.images)
        if nxt in self._next_cache or nxt == self.index:
            return

        def worker(idx, path):
            try:
                img = self._load_display_image(path)
                with self._prefetch_lock:
                    self._next_cache[idx] = img
            except Exception:
                pass

        threading.Thread(target=worker, args=(nxt, self.images[nxt]), daemon=True).start()

    def _on_resize(self, event):
        # Debounce re-render on window/monitor resize
        if self._resize_job:
            self.win.after_cancel(self._resize_job)
        self._resize_job = self.win.after(150, self._rerender_current)

    def _rerender_current(self):
        if getattr(self, "_current_pil", None) is not None:
            self._fit_and_render(self._current_pil)

    # -- navigation & playback ----------------------------------------------

    def next_image(self, manual=False):
        if not self.images:
            return
        self.index = (self.index + 1) % len(self.images)
        if self.index == 0:
            random.shuffle(self.images)
            self._next_cache.clear()
        self._show_current()
        if manual:
            self._restart_timer()

    def prev_image(self, manual=False):
        if not self.images:
            return
        self.index = (self.index - 1) % len(self.images)
        self._next_cache.clear()
        self._show_current()
        if manual:
            self._restart_timer()

    def toggle_play(self):
        self.playing = not self.playing
        self.play_btn.config(text="⏸ Pause" if self.playing else "▶ Play")
        if self.playing:
            self._schedule_advance()
        elif self._after_id:
            self.win.after_cancel(self._after_id)
            self._after_id = None

    def adjust_interval(self, delta):
        self.interval = max(1, self.interval + delta)
        self.interval_label.config(text=f"{self.interval}s")
        cfg = load_config()
        cfg["interval"] = self.interval
        save_config(cfg)
        if self.playing:
            self._restart_timer()

    def _schedule_advance(self):
        if self._after_id:
            self.win.after_cancel(self._after_id)
        self._after_id = self.win.after(self.interval * 1000, self._tick)

    def _restart_timer(self):
        if self.playing:
            self._schedule_advance()

    def _tick(self):
        if self.playing:
            self.next_image()
            self._schedule_advance()

    # -- controls overlay auto-hide ------------------------------------------

    def _on_activity(self, _event=None):
        if not self.controls.winfo_ismapped():
            self.controls.place(relx=0.5, rely=1.0, anchor="s", y=-16)
        self._schedule_hide_controls()

    def _schedule_hide_controls(self):
        if self._hide_controls_id:
            self.win.after_cancel(self._hide_controls_id)
        self.controls.place(relx=0.5, rely=1.0, anchor="s", y=-16)
        self._hide_controls_id = self.win.after(CONTROLS_HIDE_DELAY_MS, self._hide_controls)

    def _hide_controls(self):
        self.controls.place_forget()

    def close(self):
        if self._after_id:
            self.win.after_cancel(self._after_id)
        if self._hide_controls_id:
            self.win.after_cancel(self._hide_controls_id)
        self.win.destroy()
        self.on_close()


def main():
    root = tk.Tk()
    SetupWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
