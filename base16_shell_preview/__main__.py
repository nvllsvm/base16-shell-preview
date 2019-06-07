import argparse
import curses
import os
import subprocess

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

    def run_script(self):
        subprocess.Popen([SHELL, self.path])

    def install_theme(self):
        if os.path.exists(THEME_PATH):
            os.remove(THEME_PATH)
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


class PreviewWindow(object):
    def __init__(self, lines, cols, *args, **kwargs):
        self.lines = lines
        self.cols = cols
        self.window = curses.newwin(lines, cols, *args, **kwargs)

    def render(self):
        for i in range(NUM_COLORS):
            curses.init_pair(i, i, -1)
            text = 'color{:02d} '.format(i)
            spaces = self.cols - len(text) - 1

            self.window.addstr(i, len(text), spaces*' ',
                               curses.color_pair(i) + curses.A_REVERSE)
            self.window.addstr(i, 0, text, curses.color_pair(i))

        self.window.refresh()


class ScrollListWindow(object):
    def __init__(self, lines, cols, *args, **kwargs):
        self.lines = lines
        self.cols = cols

        self.offset = 0
        self.selected = 0
        self.window = curses.newwin(lines, cols, **kwargs)
        self.data = []

    def set_data(self, data):
        self.data = data

    def up(self):
        if self.selected > 0:
            self.selected -= 1
        elif self.offset != 0:
            self.offset -= 1
        self.render()

    def down(self):
        if (self.offset + self.selected) > (len(self.data) - 2):
            pass
        elif self.selected == (self.lines - 1):
            self.offset += 1
        else:
            self.selected += 1
        self.render()

    def up_page(self):
        for i in range(NUM_COLORS):
            self.up()

    def down_page(self):
        for i in range(NUM_COLORS):
            self.down()

    def top(self):
        for i in range(len(self.data)):
            self.up()

    def bottom(self):
        for i in range(len(self.data)):
            self.down()

    def render(self):
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

            self.window.addstr(line, 0, (self.cols - 1) * ' ', attrs)
            self.window.addstr(line, 0, value[:self.cols-1], attrs)
            line += 1

        self.window.refresh()


def run_curses_app(scripts_dir):
    stdscr = curses.initscr()
    stdscr.refresh()
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.noecho()

    themes = {s.name: s for s in get_themes(scripts_dir)}

    scroll_list_cols = 35
    preview_cols = 42

    total_cols = scroll_list_cols + preview_cols

    scroll_list_win = ScrollListWindow(NUM_COLORS, scroll_list_cols)
    preview_win = PreviewWindow(NUM_COLORS, preview_cols, 0, scroll_list_cols)

    preview_win.render()

    scroll_list_win.set_data(sorted(themes.keys()))
    scroll_list_win.render()

    themes[scroll_list_win.value].run_script()

    while True:
        scroll_list_win.render()
        preview_win.render()
        c = stdscr.getch()

        if c == curses.KEY_DOWN:
            scroll_list_win.down()
            themes[scroll_list_win.value].run_script()
        elif c == curses.KEY_UP:
            scroll_list_win.up()
            themes[scroll_list_win.value].run_script()
        elif c == curses.KEY_PPAGE:
            scroll_list_win.up_page()
            themes[scroll_list_win.value].run_script()
        elif c == curses.KEY_NPAGE:
            scroll_list_win.down_page()
            themes[scroll_list_win.value].run_script()
        elif c == curses.KEY_HOME:
            scroll_list_win.top()
            themes[scroll_list_win.value].run_script()
        elif c == curses.KEY_END:
            scroll_list_win.bottom()
            themes[scroll_list_win.value].run_script()
        elif c == ord('q'):
            end_run()
            return
        elif c == ord('\n'):
            theme = themes[scroll_list_win.value]
            theme.install_theme()
            end_run(theme)
            return
        elif c == curses.KEY_RESIZE:
            if curses.LINES < NUM_COLORS:
                raise ValueError('Terminal has less than 22 lines.')
            elif curses.COLS < total_cols:
                raise ValueError('Terminal has less than {} cols.'.format(
                    total_cols))


def end_run(theme=None):
    if theme is None:
        theme = Theme(THEME_PATH)
    try:
        curses.endwin()
        theme.run_script()
    except KeyboardInterrupt:
        end_run()


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
    parser.parse_args()

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

    try:
        run_curses_app(scripts_dir)
    except KeyboardInterrupt:
        end_run()


if __name__ == '__main__':
    main()
