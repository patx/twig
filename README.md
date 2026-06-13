# Twig

Twig is a small GTK code editor intended for lightweight Linux desktops such
as CrunchBang++. It focuses on the basics: one file per window, open/save,
syntax highlighting, line numbers, find/replace, undo/redo, dirty indicators,
and save-before-close prompts.

Repository: <https://github.com/patx/twig>

## Dependencies

On CrunchBang++ or Debian-based systems:

```sh
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-4
```

Some older systems package GtkSourceView 3 instead:

```sh
sudo apt install gir1.2-gtksource-3.0
```

## Run

```sh
./twig.py
./twig.py path/to/file.py
```

## Install

```sh
sudo make install
```

Install somewhere else:

```sh
make install PREFIX="$HOME/.local"
```

Uninstall:

```sh
sudo make uninstall
```

## Shortcuts

Twig intentionally has no toolbar or menu bar. Use these keyboard shortcuts:

| Shortcut | Action |
| --- | --- |
| `Ctrl+N` or `Ctrl+T` | Open a new empty editor window |
| `Ctrl+O` | Open one or more files |
| `Ctrl+S` | Save the current file |
| `Ctrl+Shift+S` | Save the current file as a new path |
| `Ctrl+W` | Close the current window |
| `Ctrl+P` | Print |
| `Ctrl+Q` | Quit Twig, prompting for unsaved files |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` or `Ctrl+Y` | Redo |
| `Ctrl+X` | Cut |
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Ctrl+A` | Select all |
| `Ctrl+F` | Open or focus Find and Replace |
| `Ctrl+G` or `F3` | Find next match |
| `Ctrl+Shift+G` or `Shift+F3` | Find previous match |
| `Ctrl+H` or `Ctrl+R` | Open Find and Replace with the replace field focused |
| `Ctrl+J` | Jump to line |
| `Tab` with selected lines | Indent selected lines with spaces |
| `Shift+Tab` with selected lines | Unindent selected lines |
| `Enter` in Find | Find next match |
| `Enter` in Replace | Replace current match |
