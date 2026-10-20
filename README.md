# Slideshow Presenter

A lightweight, standalone photo slideshow app for Ubuntu Linux. Pick one or
more folders, it recursively finds every image inside them, orders them the
way you choose, and plays a fullscreen slideshow. It can also be launched
directly on an image (or a batch of images) via "Open With" or a shortcut.

## Running it

1. Download `slideshow-presenter` (no Python install needed — everything is
   bundled inside).
2. Make it executable and run it:

   ```bash
   chmod +x slideshow-presenter
   ./slideshow-presenter
   ```

   Built and tested on Ubuntu 24.04 (glibc 2.39). It should run on that
   version or newer without any extra setup.

## Using it

- **Setup window**: click "Add Folder…" to add as many folders as you like
  (subfolders are scanned too). Set the interval, display order, and
  whether to show captions, then click "Start Slideshow". The window sizes
  itself to fit everything automatically — no manual resizing needed. Your
  settings are remembered for next time
  (`~/.config/slideshow-presenter/config.json`).
- **Order**: choose how images are sequenced —
  - *Shuffle (random)* — shuffled at the start, and reshuffled each time it
    loops back to the beginning so long runs keep feeling fresh.
  - *Name (A→Z)* — alphabetical by filename, stays in that stable order.
  - *Date (newest first)* / *Date (oldest first)* — by file modification
    time, stays in that stable order.
- **During the slideshow**:
  - Move the mouse to reveal the control bar (auto-hides after ~2.5s).
  - `Space` — play/pause · `←` / `→` — previous/next image · `Esc` — exit.
  - The control bar also has Prev/Play-Pause/Next buttons, `+`/`−` to adjust
    the interval on the fly, an image counter, and an Exit button.
  - Corrupt/unreadable image files are skipped automatically.

Supported formats: JPG, PNG, GIF, BMP, TIFF, WEBP.

## Opening it as a shortcut / "Open With" on images

The app accepts file and folder paths as command-line arguments, which lets
you launch it straight into a fullscreen slideshow instead of the setup
screen:

```bash
./slideshow-presenter /path/to/photo.jpg        # whole folder, starting on this photo
./slideshow-presenter photo1.jpg photo2.jpg ...  # exactly this set of photos
./slideshow-presenter /path/to/folder            # everything in that folder
```

- **One image** → shows every image in that image's folder, starting on the
  one you picked.
- **Several images** (e.g. multi-selected in a file manager) → shows
  exactly that set, in your chosen order.
- A **folder** → behaves like adding that folder in the setup window.

It uses your last-saved interval/order/caption settings, and `Esc` quits
the app entirely (there's no setup window to return to in this mode).

### Add it to your app menu / "Open With" list

```bash
mkdir -p ~/.local/bin ~/.local/share/applications
cp slideshow-presenter ~/.local/bin/
chmod +x ~/.local/bin/slideshow-presenter

cat > ~/.local/share/applications/slideshow-presenter.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Slideshow Presenter
Comment=Shuffle-play photos from multiple folders as a fullscreen slideshow
Exec=$HOME/.local/bin/slideshow-presenter %F
Icon=image-x-generic
Terminal=false
Categories=Graphics;Photography;
MimeType=image/jpeg;image/png;image/gif;image/bmp;image/tiff;image/webp;
EOF

update-desktop-database ~/.local/share/applications
```

After that, right-click any image in your file manager → "Open With" →
"Slideshow Presenter" will appear in the list. You can also set it as the
*default* app for a given image type with:

```bash
xdg-mime default slideshow-presenter.desktop image/jpeg
```

(repeat for other mime types, e.g. `image/png`, as you like).

### Desktop icon (optional)

To also put a launchable icon on your Desktop:

```bash
cp ~/.local/share/applications/slideshow-presenter.desktop ~/Desktop/
chmod +x ~/Desktop/slideshow-presenter.desktop
gio set ~/Desktop/slideshow-presenter.desktop "metadata::trusted" true
```

(The `gio set ... trusted true` step is what GNOME Files needs to let you
double-click it instead of just showing it as untrusted text.)

## Source

`main.py` is plain Python (stdlib `tkinter` + `Pillow`), included alongside
the binary if you ever want to tweak behavior and rebuild:

```bash
pip3 install pillow pyinstaller          # needs python3-tk: sudo apt install python3-tk
pyinstaller --onefile --windowed --hidden-import=PIL._tkinter_finder main.py
```

(The `--hidden-import=PIL._tkinter_finder` flag matters — without it the
packaged binary fails to draw images at all.)
