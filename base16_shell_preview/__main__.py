import argparse
import curses
import os
import signal
import subprocess
import sys

try:
    import pkg_resources
    VERSION = pkg_resources.get_distribution('base16-shell-preview').version
except Exception:
    VERSION = 'unknown'

THEME_PATH = os.path.expanduser('~/.base16_theme')

SHELL = '/bin/sh'

NUM_COLORS = 22

DEVNULL = open(os.devnull, 'w')


def get_themes(scripts_dir):
    return [Theme(os.path.join(scripts_dir, f))
            for f in sorted(os.listdir(scripts_dir))]


class Theme(object):
    def __init__(self, path):
        self.path = path
        filename = os.path.split(self.path)[1]
        self.name = filename.replace('base16-', '', 1)[:-3]

    def apply(self):
        subprocess.Popen([SHELL, self.path])

    def install(self):
        try:
            os.remove(THEME_PATH)
        except FileNotFoundError:
            pass
        os.symlink(self.path, THEME_PATH)

        hooks_dir = os.environ.get('BASE16_SHELL_HOOKS')
        if hooks_dir and os.path.isdir(hooks_dir):
            env = os.environ.copy()
            env['BASE16_THEME'] = self.name
            for name in os.listdir(hooks_dir):
                path = os.path.join(hooks_dir, name)
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    subprocess.Popen(
                        [path],
                        env=env,
                        stderr=DEVNULL,
                        stdout=DEVNULL
                    )

    @property
    def bg_color(self):
        with open(self.path) as f:
            lines = f.readlines()
        background_line = [
            line
            for line in lines
            if line.startswith('color00')
        ][0]
        background_str = background_line.split('"')[1].replace('/', '')
        return hex(int(background_str, 16))


class ScrollListWindow(object):
    def __init__(self, data, lines, left_cols, right_cols):
        self.data = data

        self.lines = lines
        self.left_cols = left_cols
        self.right_cols = right_cols

        self.offset = 0
        self.selected = 0
        self.left_window = curses.newwin(lines, left_cols)
        self.right_window = curses.newwin(lines, right_cols, 0, self.left_cols)

    def up(self):
        self.index -= 1
        self.render()

    @property
    def index(self):
        return self.offset + self.selected

    @index.setter
    def index(self, index):
        if index < 0:
            index = 0
        elif index >= len(self.data):
            index = len(self.data) - 1

        if index < (self.index):
            diff = self.index - index

            available = self.selected
            self.selected -= min(diff, available)
        elif index > (self.index):
            diff = index - self.index

            available = self.lines - 1 - self.selected
            self.selected += min(diff, available)

        self.offset = index - self.selected

    def down(self):
        self.index += 1
        self.render()

    def up_page(self):
        self.selected = 0
        self.index -= self.lines
        self.render()

    def down_page(self):
        self.selected = self.lines - 1
        self.index += self.lines
        self.render()

    def top(self):
        self.index = 0
        self.render()

    def bottom(self):
        self.index = len(self.data) - 1
        self.render()

    def render(self):
        self._render_left()
        self._render_right()
        self.left_window.refresh()
        self.right_window.refresh()

    def _render_left(self):
        end = self.offset + self.lines
        line = 0
        for i, value in enumerate(self.data):
            if i < self.offset:
                continue
            elif i == end:
                break

            if line == self.selected:
                self.value = value
                attrs = curses.A_REVERSE
            else:
                attrs = 0

            self.left_window.addstr(
                line, 0, (self.left_cols - 1) * ' ', attrs)
            self.left_window.addstr(
                line, 0, self.format_left(value)[:self.left_cols-1],
                attrs)
            line += 1

    def _render_right(self):
        for i in range(self.lines):
            curses.init_pair(i, i, -1)
            text = 'color{:02d} '.format(i)
            spaces = self.right_cols - len(text) - 1

            self.right_window.addstr(i, len(text), spaces*' ',
                                     curses.color_pair(i) + curses.A_REVERSE)
            self.right_window.addstr(i, 0, text, curses.color_pair(i))


class ThemePreviewer(ScrollListWindow):

    @staticmethod
    def format_left(theme):
        return theme.name

    @staticmethod
    def format_right(theme):
        pass

    def render(self):
        super().render()
        self.value.apply()


def run_curses_app(stdscr, scripts_dir, sort_bg):
    stdscr.refresh()
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.noecho()

    sort_key = 'bg_color' if sort_bg else 'name'
    sorted_themes = sorted(
        get_themes(scripts_dir),
        key=lambda x: (getattr(x, sort_key), x.name)
    )

    scroll_list_cols = 35
    preview_cols = 42

    total_cols = scroll_list_cols + preview_cols

    win = ThemePreviewer(
        sorted_themes,
        NUM_COLORS,
        scroll_list_cols,
        preview_cols,
    )

    win.render()

    movement_map = {
        curses.KEY_DOWN: win.down,
        curses.KEY_UP: win.up,
        curses.KEY_PPAGE: win.up_page,
        curses.KEY_NPAGE: win.down_page,
        curses.KEY_HOME: win.top,
        curses.KEY_END: win.bottom,
    }

    while True:
        win.render()
        c = stdscr.getch()

        if c in movement_map:
            movement_map[c]()
        elif c == ord('q'):
            end_run()
            return
        elif c == ord('\n'):
            win.value.install()
            end_run()
            return
        elif c == curses.KEY_RESIZE:
            if curses.LINES < win.lines:
                raise ValueError('Terminal has less than 22 lines.')
            elif curses.COLS < total_cols:
                raise ValueError('Terminal has less than {} cols.'.format(
                    total_cols))


def end_run(*_):
    curses.endwin()
    if os.path.exists(THEME_PATH):
        Theme(THEME_PATH).apply()


def _exit_signal_handler(*_):
    end_run()
    sys.exit()


def main():
    parser = argparse.ArgumentParser(
        'base16-shell-preview',
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
keys:
  up/down      move 1
  pgup/pgdown  move page
  home/end     go to beginning/end
  q            quit
  enter        enable theme and quit
""")
    parser.add_argument(
        '--version',
        action='version',
        version=VERSION
    )
    parser.add_argument(
        '--sort-bg',
        action='store_true',
        help='sort themes by background (darkest to lightest)'
    )
    args = parser.parse_args()

    for signalnum in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(signalnum, _exit_signal_handler)

    base16_shell_dir = os.environ.get('BASE16_SHELL')
    if not base16_shell_dir:
        if os.path.islink(THEME_PATH):
            base16_shell_dir = os.path.dirname(
                os.path.dirname(
                    os.readlink(THEME_PATH)
                    )
            )
    if not base16_shell_dir:
        parser.error(
            'please set the BASE16_SHELL environment variable '
            'to the local repository path.'
        )

    scripts_dir = os.path.join(base16_shell_dir, 'scripts')

    curses.wrapper(run_curses_app, scripts_dir, args.sort_bg)


if __name__ == '__main__':
    main()
