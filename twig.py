#!/usr/bin/env python3
"""Twig: a tiny GTK code editor for lightweight Linux desktops."""

import sys
from pathlib import Path

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gio, GLib, Gtk

    try:
        gi.require_version("GtkSource", "4")
    except ValueError:
        gi.require_version("GtkSource", "3.0")
    from gi.repository import GtkSource
except (ImportError, ValueError) as exc:
    print(
        "Twig requires GTK 3, PyGObject, and GtkSourceView.\n"
        "On CrunchBang++/Debian, install:\n"
        "  sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-4\n"
        f"\nStartup error: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)


APP_ID = "io.github.patx.twig"
UNTITLED = "Untitled"


def read_text_file(path):
    data = Path(path).read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace"), "utf-8"


def write_text_file(path, text, encoding):
    target_encoding = encoding or "utf-8"
    try:
        Path(path).write_text(text, encoding=target_encoding)
        return target_encoding
    except UnicodeEncodeError:
        Path(path).write_text(text, encoding="utf-8")
        return "utf-8"


def install_css():
    css = b"""
    entry {
        font: 10pt sans;
    }

    textview, textview text {
        background: #1f2329;
        color: #d8dee9;
        font: 10pt monospace;
    }

    textview border {
        background: #181b20;
        color: #7f8a99;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


class TwigWindow(Gtk.ApplicationWindow):
    def __init__(self, app, path=None):
        super().__init__(application=app)
        self.app = app
        self.path = Path(path).resolve() if path else None
        self.encoding = "utf-8"
        self.find_dialog = None
        self.buffer = GtkSource.Buffer()
        self.view = GtkSource.View.new_with_buffer(self.buffer)

        self.set_default_size(920, 640)
        self._build_actions()
        self._build_ui()
        self._configure_editor()
        self.buffer.connect("modified-changed", lambda _buffer: self.update_title())
        self.connect("delete-event", self._on_delete_event)

        if self.path:
            self.load()
        else:
            self.apply_language()
            self.buffer.set_modified(False)
            self.update_title()

    @property
    def title_name(self):
        return self.path.name if self.path else UNTITLED

    def _build_actions(self):
        actions = {
            "new": self.on_new,
            "open": self.on_open,
            "save": self.on_save,
            "save-as": self.on_save_as,
            "close": self.on_close,
            "print": self.on_print,
            "find": self.on_find,
            "find-next": self.on_find_next,
            "find-prev": self.on_find_prev,
            "replace": self.on_replace,
            "jump-to": self.on_jump_to,
            "undo": self.on_undo,
            "redo": self.on_redo,
            "cut": self.on_cut,
            "copy": self.on_copy,
            "paste": self.on_paste,
            "select-all": self.on_select_all,
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        scroller.add(self.view)
        root.pack_start(scroller, True, True, 0)

        self.add(root)
        self.show_all()
        self.view.grab_focus()

    def _configure_editor(self):
        self.view.set_show_line_numbers(True)
        self.view.set_monospace(True)
        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(True)
        self.view.set_auto_indent(True)
        self.view.set_highlight_current_line(False)
        self.view.connect("key-press-event", self.on_key_press)

        if hasattr(self.buffer, "set_max_undo_levels"):
            self.buffer.set_max_undo_levels(-1)
        self.buffer.set_highlight_syntax(True)

        style_manager = GtkSource.StyleSchemeManager.get_default()
        for scheme_id in ("oblivion", "solarized-dark", "classic"):
            scheme = style_manager.get_scheme(scheme_id)
            if scheme:
                self.buffer.set_style_scheme(scheme)
                break

    def apply_language(self):
        manager = GtkSource.LanguageManager.get_default()
        if not self.path:
            self.buffer.set_language(None)
            return

        filename = str(self.path)
        content_type = None
        if self.path.exists():
            content_type, _uncertain = Gio.content_type_guess(filename, None)
        self.buffer.set_language(manager.guess_language(filename, content_type))

    def load(self):
        try:
            text, self.encoding = read_text_file(self.path)
        except OSError as exc:
            self.show_error("Open failed", str(exc))
            self.path = None
            text = ""
        self.buffer.set_text(text)
        self.apply_language()
        self.buffer.set_modified(False)
        self.buffer.place_cursor(self.buffer.get_start_iter())
        self.update_title()

    def save(self, path=None):
        if path:
            self.path = Path(path).resolve()
        if not self.path:
            return self.save_as()

        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        text = self.buffer.get_text(start, end, True)
        try:
            self.encoding = write_text_file(self.path, text, self.encoding)
        except (OSError, UnicodeError) as exc:
            self.show_error("Save failed", str(exc))
            return False

        self.apply_language()
        self.buffer.set_modified(False)
        self.update_title()
        return True

    def save_as(self):
        dialog = Gtk.FileChooserDialog(
            title="Save File",
            transient_for=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.OK)
        dialog.set_do_overwrite_confirmation(True)
        if self.path:
            dialog.set_filename(str(self.path))
        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or not filename:
            return False
        return self.save(filename)

    def confirm_save(self):
        if not self.buffer.get_modified():
            return True

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Save changes to {self.title_name}?",
        )
        dialog.format_secondary_text("Unsaved changes will be lost if you discard them.")
        dialog.add_buttons(
            "_Cancel",
            Gtk.ResponseType.CANCEL,
            "_Discard",
            Gtk.ResponseType.NO,
            "_Save",
            Gtk.ResponseType.YES,
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            return self.save()
        if response == Gtk.ResponseType.NO:
            return True
        return False

    def selected_text(self):
        if not self.buffer.get_has_selection():
            return ""
        start, end = self.buffer.get_selection_bounds()
        return self.buffer.get_text(start, end, True)

    def find_text(self, needle, forward=True):
        if not needle:
            return False

        flags = Gtk.TextSearchFlags.CASE_INSENSITIVE
        insert = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        match = insert.forward_search(needle, flags, None) if forward else insert.backward_search(needle, flags, None)
        if not match:
            edge = self.buffer.get_start_iter() if forward else self.buffer.get_end_iter()
            match = edge.forward_search(needle, flags, None) if forward else edge.backward_search(needle, flags, None)
        if not match:
            return False

        start, end = match
        if forward:
            self.buffer.select_range(end, start)
        else:
            self.buffer.select_range(start, end)
        self.view.scroll_to_iter(start, 0.15, False, 0.0, 0.0)
        return True

    def replace_selection(self, needle, replacement):
        if not needle or not self.buffer.get_has_selection():
            return False

        start, end = self.buffer.get_selection_bounds()
        selected = self.buffer.get_text(start, end, True)
        if selected.lower() != needle.lower():
            return False

        self.buffer.begin_user_action()
        self.buffer.delete(start, end)
        self.buffer.insert_at_cursor(replacement)
        self.buffer.end_user_action()
        return True

    def replace_current(self, needle, replacement):
        if not needle:
            return False
        if not self.replace_selection(needle, replacement):
            if not self.find_text(needle, True):
                return False
            if not self.replace_selection(needle, replacement):
                return False
        self.find_text(needle, True)
        return True

    def replace_all(self, needle, replacement):
        if not needle:
            return 0

        count = 0
        flags = Gtk.TextSearchFlags.CASE_INSENSITIVE
        self.buffer.begin_user_action()
        cursor = self.buffer.get_start_iter()
        while True:
            match = cursor.forward_search(needle, flags, None)
            if not match:
                break
            start, end = match
            next_offset = start.get_offset() + len(replacement)
            self.buffer.delete(start, end)
            self.buffer.insert(start, replacement)
            cursor = self.buffer.get_iter_at_offset(next_offset)
            count += 1
        self.buffer.end_user_action()

        return count

    def selected_line_bounds(self):
        start, end = self.buffer.get_selection_bounds()
        if start.compare(end) > 0:
            start, end = end, start
        line_start = self.buffer.get_iter_at_line(start.get_line())
        last_line = end.get_line()
        if end.starts_line() and end.compare(start) != 0:
            last_line -= 1
        return line_start, max(start.get_line(), last_line)

    def indent_selection(self):
        if not self.buffer.get_has_selection():
            return False

        start, last_line = self.selected_line_bounds()
        self.buffer.begin_user_action()
        for line in range(start.get_line(), last_line + 1):
            line_iter = self.buffer.get_iter_at_line(line)
            self.buffer.insert(line_iter, " " * self.view.get_tab_width())
        self.buffer.end_user_action()
        return True

    def unindent_selection(self):
        if not self.buffer.get_has_selection():
            return False

        start, last_line = self.selected_line_bounds()
        self.buffer.begin_user_action()
        for line in range(start.get_line(), last_line + 1):
            line_start = self.buffer.get_iter_at_line(line)
            line_end = line_start.copy()
            removed = 0
            while removed < self.view.get_tab_width() and not line_end.ends_line():
                char = line_end.get_char()
                if char == " ":
                    line_end.forward_char()
                    removed += 1
                elif char == "\t":
                    line_end.forward_char()
                    removed += self.view.get_tab_width()
                    break
                else:
                    break
            if line_start.compare(line_end) != 0:
                self.buffer.delete(line_start, line_end)
        self.buffer.end_user_action()
        return True

    def jump_to_line(self, line_number):
        line_count = self.buffer.get_line_count()
        line_index = max(0, min(line_number - 1, line_count - 1))
        line_iter = self.buffer.get_iter_at_line(line_index)
        self.buffer.place_cursor(line_iter)
        self.view.scroll_to_iter(line_iter, 0.2, False, 0.0, 0.0)

    def open_files(self, paths):
        for index, path in enumerate(paths):
            if index == 0 and self.is_empty_untitled():
                self.path = Path(path).resolve()
                self.load()
            else:
                self.app.open_window(path)

    def is_empty_untitled(self):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        return not self.path and not self.buffer.get_modified() and not self.buffer.get_text(start, end, True)

    def update_title(self):
        dirty = "*" if self.buffer.get_modified() else ""
        name = str(self.path) if self.path else self.title_name
        self.set_title(f"{dirty}{name} - Twig")

    def show_error(self, title, detail):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()

    def on_new(self, *_args):
        self.app.open_window()

    def on_open(self, *_args):
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        response = dialog.run()
        filenames = dialog.get_filenames()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.open_files(filenames)

    def on_save(self, *_args):
        self.save()

    def on_save_as(self, *_args):
        self.save_as()

    def on_close(self, *_args):
        self.close()

    def on_print(self, *_args):
        compositor = GtkSource.PrintCompositor.new_from_view(self.view)
        compositor.set_print_line_numbers(5)
        operation = Gtk.PrintOperation()
        operation.connect("paginate", lambda _operation, context: compositor.paginate(context))
        operation.connect("draw-page", lambda _operation, context, page: compositor.draw_page(context, page))

        def on_begin_print(_operation, context):
            while not compositor.paginate(context):
                pass
            operation.set_n_pages(compositor.get_n_pages())

        operation.connect("begin-print", on_begin_print)
        try:
            operation.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)
        except GLib.Error as exc:
            self.show_error("Print failed", str(exc))

    def on_find(self, *_args):
        if self.find_dialog:
            self.find_dialog.present()
            return
        self.find_dialog = FindReplaceDialog(self)
        self.find_dialog.connect("destroy", lambda _dialog: setattr(self, "find_dialog", None))
        self.find_dialog.show_all()

    def on_find_next(self, *_args):
        if self.find_dialog:
            self.find_dialog.find_next()
        else:
            self.on_find()

    def on_find_prev(self, *_args):
        if self.find_dialog:
            self.find_dialog.find_previous()
        else:
            self.on_find()

    def on_replace(self, *_args):
        self.on_find()
        if self.find_dialog:
            self.find_dialog.replace_entry.grab_focus()

    def on_jump_to(self, *_args):
        dialog = JumpToDialog(self)
        dialog.show_all()

    def on_undo(self, *_args):
        if self.buffer.can_undo():
            self.buffer.undo()

    def on_redo(self, *_args):
        if self.buffer.can_redo():
            self.buffer.redo()

    def on_cut(self, *_args):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.buffer.cut_clipboard(clipboard, True)

    def on_copy(self, *_args):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.buffer.copy_clipboard(clipboard)

    def on_paste(self, *_args):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.buffer.paste_clipboard(clipboard, None, True)

    def on_select_all(self, *_args):
        self.buffer.select_range(self.buffer.get_start_iter(), self.buffer.get_end_iter())

    def on_key_press(self, _view, event):
        if event.keyval == Gdk.KEY_Tab and self.buffer.get_has_selection():
            return self.indent_selection()
        if event.keyval in (Gdk.KEY_ISO_Left_Tab, Gdk.KEY_Tab) and event.state & Gdk.ModifierType.SHIFT_MASK:
            if self.buffer.get_has_selection():
                return self.unindent_selection()
        return False

    def _on_delete_event(self, *_args):
        return not self.confirm_save()


class FindReplaceDialog(Gtk.Window):
    def __init__(self, editor):
        super().__init__(title="Find and Replace", transient_for=editor, modal=False)
        self.editor = editor
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_resizable(False)
        self.set_border_width(8)

        self.find_entry = Gtk.Entry()
        self.replace_entry = Gtk.Entry()
        self.status = Gtk.Label(xalign=0)

        selected = editor.selected_text()
        if selected and "\n" not in selected:
            self.find_entry.set_text(selected)

        self._build_ui()
        self.find_entry.connect("activate", lambda _entry: self.find_next())
        self.replace_entry.connect("activate", lambda _entry: self.replace_current())

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)

        grid.attach(Gtk.Label(label="Find", xalign=0), 0, 0, 1, 1)
        grid.attach(self.find_entry, 1, 0, 4, 1)
        grid.attach(Gtk.Label(label="Replace", xalign=0), 0, 1, 1, 1)
        grid.attach(self.replace_entry, 1, 1, 4, 1)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        buttons.pack_start(self._button("Previous", lambda _button: self.find_previous()), False, False, 0)
        buttons.pack_start(self._button("Next", lambda _button: self.find_next()), False, False, 0)
        buttons.pack_start(self._button("Replace", lambda _button: self.replace_current()), False, False, 0)
        buttons.pack_start(self._button("Replace All", lambda _button: self.replace_all()), False, False, 0)
        buttons.pack_start(self._button("Close", lambda _button: self.destroy()), False, False, 0)

        outer.pack_start(grid, False, False, 0)
        outer.pack_start(buttons, False, False, 0)
        outer.pack_start(self.status, False, False, 0)
        self.add(outer)

    def _button(self, label, callback):
        button = Gtk.Button(label=label)
        button.connect("clicked", callback)
        return button

    def needle(self):
        return self.find_entry.get_text()

    def replacement(self):
        return self.replace_entry.get_text()

    def find_next(self):
        found = self.editor.find_text(self.needle(), True)
        self.status.set_text("" if found else "No matches")

    def find_previous(self):
        found = self.editor.find_text(self.needle(), False)
        self.status.set_text("" if found else "No matches")

    def replace_current(self):
        replaced = self.editor.replace_current(self.needle(), self.replacement())
        self.status.set_text("" if replaced else "No match selected")

    def replace_all(self):
        count = self.editor.replace_all(self.needle(), self.replacement())
        self.status.set_text(f"Replaced {count} match" + ("" if count == 1 else "es"))


class JumpToDialog(Gtk.Window):
    def __init__(self, editor):
        super().__init__(title="Jump To", transient_for=editor, modal=False)
        self.editor = editor
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_resizable(False)
        self.set_border_width(8)

        self.line_entry = Gtk.SpinButton()
        self.line_entry.set_range(1, max(1, editor.buffer.get_line_count()))
        self.line_entry.set_increments(1, 10)
        self.line_entry.set_value(editor.buffer.get_iter_at_mark(editor.buffer.get_insert()).get_line() + 1)
        self.line_entry.connect("activate", lambda _entry: self.jump())

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.pack_start(Gtk.Label(label="Line", xalign=0), False, False, 0)
        row.pack_start(self.line_entry, True, True, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        jump_button = Gtk.Button(label="Jump")
        close_button = Gtk.Button(label="Close")
        jump_button.connect("clicked", lambda _button: self.jump())
        close_button.connect("clicked", lambda _button: self.destroy())
        buttons.pack_start(jump_button, False, False, 0)
        buttons.pack_start(close_button, False, False, 0)

        outer.pack_start(row, False, False, 0)
        outer.pack_start(buttons, False, False, 0)
        self.add(outer)
        self.line_entry.grab_focus()

    def jump(self):
        self.editor.jump_to_line(self.line_entry.get_value_as_int())
        self.destroy()


class TwigApp(Gtk.Application):
    def __init__(self, initial_files):
        flags = Gio.ApplicationFlags.NON_UNIQUE | Gio.ApplicationFlags.HANDLES_OPEN
        super().__init__(application_id=APP_ID, flags=flags)
        self.initial_files = initial_files

    def do_startup(self):
        Gtk.Application.do_startup(self)
        install_css()

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)

        shortcuts = {
            "win.new": ["<Primary>n", "<Primary>t"],
            "win.open": ["<Primary>o"],
            "win.save": ["<Primary>s"],
            "win.save-as": ["<Primary><Shift>s"],
            "win.close": ["<Primary>w"],
            "app.quit": ["<Primary>q"],
            "win.print": ["<Primary>p"],
            "win.find": ["<Primary>f"],
            "win.replace": ["<Primary>h", "<Primary>r"],
            "win.find-next": ["F3", "<Primary>g"],
            "win.find-prev": ["<Shift>F3", "<Primary><Shift>g"],
            "win.jump-to": ["<Primary>j"],
            "win.undo": ["<Primary>z"],
            "win.redo": ["<Primary>y", "<Primary><Shift>z"],
            "win.cut": ["<Primary>x"],
            "win.copy": ["<Primary>c"],
            "win.paste": ["<Primary>v"],
            "win.select-all": ["<Primary>a"],
        }
        for action, accels in shortcuts.items():
            self.set_accels_for_action(action, accels)

    def do_activate(self):
        if self.initial_files:
            for path in self.initial_files:
                self.open_window(path)
            self.initial_files = []
        elif not self.get_windows():
            self.open_window()

    def do_open(self, files, _n_files, _hint):
        for file in files:
            self.open_window(file.get_path())

    def open_window(self, path=None):
        window = TwigWindow(self, path)
        window.present()
        return window

    def on_quit(self, *_args):
        for window in list(self.get_windows()):
            window.close()
            if window in self.get_windows():
                break


def main(argv):
    files = [arg for arg in argv[1:] if not arg.startswith("-")]
    app = TwigApp(files)
    return app.run(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
