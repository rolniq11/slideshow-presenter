# Slideshow Presenter

A lightweight, standalone photo slideshow app for Ubuntu Linux. Pick one or
more folders, it recursively finds every image inside them, shuffles them,
and plays a fullscreen slideshow.

## Running it

1. Download `slideshow-presenter` (no Python install needed — everything is
   bundled inside).
2. Make it executable and run it:

   ```bash
   chmod +x slideshow-presenter
   ./slideshow-presenter
   ```

   Built and tested on Ubuntu 24.04 (glibc 2.39). It should run on that
   version or newer without any extra setup. If your machine is on an older
   Ubuntu release and the binary won't launch, let me know and I can rebuild
   from `main.py` for it — or you can build it yourself there with:
   `pip3 install pillow pyinstaller && pyinstaller --onefile --windowed main.py`
   (needs `python3-tk` installed via `sudo apt install python3-tk`).

## Using it

- **Setup window**: click "Add Folder…" to add as many folders as you like
  (subfolders are scanned too). Set the interval and whether to show
  captions, then click "Start Slideshow". Your folder list, interval, and
  caption preference are remembered for next time
  (`~/.config/slideshow-presenter/config.json`).
- **During the slideshow**:
  - Move the mouse to reveal the control bar (auto-hides after ~2.5s).
  - `Space` — play/pause · `←` / `→` — previous/next image · `Esc` — exit.
  - The control bar also has Prev/Play-Pause/Next buttons, `+`/`−` to adjust
    the interval on the fly, an image counter, and an Exit button.
  - Images are shuffled at the start and reshuffled each time the deck loops
    back to the beginning, so the order keeps feeling fresh on long runs.
  - Corrupt/unreadable image files are skipped automatically.

Supported formats: JPG, PNG, GIF, BMP, TIFF, WEBP.

## Source

`main.py` is plain Python (stdlib `tkinter` + `Pillow`), included alongside
the binary if you ever want to tweak behavior (transition style, default
interval, etc.) and rebuild.
